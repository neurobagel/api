import re
from typing import ClassVar, Literal

from pydantic import BaseModel

CAMEL_TO_SNAKE_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")
SPARQL_SELECTED_VARS = [
    "dataset",
    "subject",
]


def to_snake(name: str) -> str:
    """Convert a PascalCase class name to a snake_case SPARQL variable without separating digits."""
    return CAMEL_TO_SNAKE_PATTERN.sub("_", name).lower()


def format_value(value):
    """Returns the SPARQL-formatted representation of a value."""
    if isinstance(value, str):
        # If the value looks like a URI or a variable, return as is
        if ":" in value or value.startswith("?"):
            return value
        return f'"{value}"'


def get_select_variables(variables: list[str]) -> str:
    """Returns the SELECT variables for the SPARQL query as a space-separated string."""
    return " ".join(f"?{var}" for var in variables)


class SPARQLSerializable(BaseModel):
    # Whether to use numbered variables for nested objects of this class in the SPARQL query.
    # If True, the first object will be represented as ?class_name1, the second as ?class_name2, etc.
    use_numbered_var: ClassVar[bool] = False

    def to_triples(self, var_name: str) -> list[str]:
        """
        Recursively flatten a model instance into SPARQL triples,
        using the var_name as the subject, the provided field names as predicates,
        and the field values as objects.
        Models with a 'schemaKey' field will also include a type triple.
        """
        var_name = to_snake(var_name)
        triples = []

        if schema_key := getattr(self, "schemaKey", None):
            triples.extend([f"{var_name} a nb:{schema_key}."])

        for field in type(self).model_fields:
            if field == "schemaKey":
                continue

            value = getattr(self, field)
            predicate = f"nb:{field}"

            values = value if isinstance(value, list) else [value]

            var_count = 0
            for filter_value in values:
                if isinstance(filter_value, SPARQLSerializable):
                    # If the field contains a nested object, skip adding triples if the nested object is empty
                    # (from https://github.com/pydantic/pydantic/discussions/4613)
                    if not any(
                        filter_value.model_dump(
                            exclude_none=True, exclude_defaults=True
                        ).values()
                    ):
                        continue
                    # TODO: If we wanted to skip running the name conversion for each nested object,
                    # or be able to customize the variable name,
                    # we could add a var_name field to SPARQLSerializable and set it per class
                    snake_class_name = to_snake(
                        filter_value.__class__.__name__
                    )
                    if filter_value.use_numbered_var:
                        var_count += 1
                        nested_var = f"?{snake_class_name}{var_count}"
                    else:
                        nested_var = f"?{snake_class_name}"

                    triples.extend([f"{var_name} {predicate} {nested_var}."])
                    triples.extend(filter_value.to_triples(nested_var))

                elif isinstance(filter_value, str):
                    formatted_filter_value = format_value(filter_value)
                    triples.extend(
                        [f"{var_name} {predicate} {formatted_filter_value}."]
                    )
        return triples


class Acquisition(SPARQLSerializable):
    use_numbered_var: ClassVar[bool] = True

    hasContrastType: str | None


class Pipeline(SPARQLSerializable):
    use_numbered_var: ClassVar[bool] = True

    hasPipelineName: str | None
    hasPipelineVersion: str | None


class Age(SPARQLSerializable):
    min_age: float | None
    max_age: float | None

    def to_triples(self, var_name: str = "?age") -> list[str]:
        triples = []
        if self.min_age is not None or self.max_age is not None:
            filters = []
            if self.min_age is not None:
                filters.append(f"{var_name} >= {self.min_age}")
            if self.max_age is not None:
                filters.append(f"{var_name} <= {self.max_age}")
            filter_statement = "FILTER (" + " && ".join(filters) + ")."
            triples.extend([filter_statement])
        return triples


class PhenotypicSession(SPARQLSerializable):
    hasSex: str | None
    hasDiagnosis: list[str]
    hasAssessment: list[str]
    hasAge: Age
    # This field is included as part of PhenotypicSession so that to_triples() knows to
    # add the type triple for PhenotypicSession when this field is set
    min_num_phenotypic_sessions: int | None = None
    schemaKey: Literal["PhenotypicSession"] = "PhenotypicSession"


class ImagingSession(SPARQLSerializable):
    hasAcquisition: list[Acquisition]
    hasCompletedPipeline: list[Pipeline]
    # This field is included as part of ImagingSession so that to_triples() knows to
    # add the type triple for ImagingSession when this field is set
    min_num_imaging_sessions: int | None = None
    schemaKey: Literal["ImagingSession"] = "ImagingSession"


class Subject(SPARQLSerializable):
    hasSession: ImagingSession | PhenotypicSession
    schemaKey: Literal["Subject"] = "Subject"


class Dataset(SPARQLSerializable):
    hasSamples: Subject
    schemaKey: Literal["Dataset"] = "Dataset"

    def to_sparql(self, var_name: str = "?dataset") -> str:
        cohort_triples_list = self.to_triples(var_name)
        cohort_triples = "\n    ".join(cohort_triples_list)

        num_sessions_filter = ""
        session = self.hasSamples.hasSession
        if isinstance(session, PhenotypicSession):
            min_sessions = session.min_num_phenotypic_sessions
        elif isinstance(session, ImagingSession):
            min_sessions = session.min_num_imaging_sessions
        if min_sessions is not None:
            num_sessions_filter = "\n".join(
                [
                    f"GROUP BY {get_select_variables(SPARQL_SELECTED_VARS)}",
                    f"HAVING (COUNT(DISTINCT ?{to_snake(session.__class__.__name__)}) >= {min_sessions})",
                ]
            )

        return f"""
SELECT {get_select_variables(SPARQL_SELECTED_VARS)}
WHERE {{
    {cohort_triples}
}}
{num_sessions_filter}
""".strip()
