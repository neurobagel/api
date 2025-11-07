from typing import Literal

from pydantic import BaseModel
from pydantic.alias_generators import to_snake

SPARQL_SELECTED_VARS = [
    "dataset_uuid",
    "dataset_name",
    "dataset_portal_uri",
    "subject_uuid",
]


def format_value(value):
    """Returns the SPARQL-formatted representation of a value."""
    if isinstance(value, str):
        if ":" in value:
            return value
        return f'"{value}"'
    # TODO: Handle numeric values (e.g. for min/max age) in https://github.com/neurobagel/api/issues/488


def get_select_variables(variables: list[str]) -> str:
    """Returns the SELECT variables for the SPARQL query as a space-separated string."""
    return " ".join(f"?{var}" for var in variables)


class SPARQLSerializable(BaseModel):
    def to_sparql(self, var_name: str) -> list[str]:
        """
        Recursively flatten a model instance into SPARQL triples,
        using the var_name as the subject, the provided field names as predicates,
        and the field values as objects.
        Models with a 'schemaKey' field will also include a type triple.
        """
        var_name = to_snake(var_name)
        triples = []
        schema_key = getattr(self, "schemaKey", None)
        if schema_key:
            triples.extend([f"{var_name} a nb:{schema_key}."])

        for field in self.model_fields:
            value = getattr(self, field)
            if field == "schemaKey":
                continue

            predicate = f"nb:{field}"
            if isinstance(value, SPARQLSerializable):
                # Skip adding triples for empty nested objects (from https://github.com/pydantic/pydantic/discussions/4613)
                if not any(
                    value.model_dump(
                        exclude_none=True, exclude_defaults=True
                    ).values()
                ):
                    continue
                nested_var = f"?{to_snake(value.__class__.__name__)}"
                triples.extend([f"{var_name} {predicate} {nested_var}."])
                triples.extend(value.to_sparql(nested_var))
            elif isinstance(value, str):
                formatted_value = format_value(value)
                triples.extend([f"{var_name} {predicate} {formatted_value}."])
        return triples


class Acquisition(SPARQLSerializable):
    hasContrastType: str | None


class Pipeline(SPARQLSerializable):
    hasPipelineName: str | None
    hasPipelineVersion: str | None


class ImagingSession(SPARQLSerializable):
    hasAcquisition: Acquisition | None
    hasCompletedPipeline: Pipeline | None
    schemaKey: Literal["ImagingSession"] = "ImagingSession"
    # This field is included as part of ImagingSession so that to_sparql() knows to
    # add the type triple for ImagingSession when this field is set
    min_num_imaging_sessions: int | None = None


class Subject(SPARQLSerializable):
    hasSession: ImagingSession | None
    schemaKey: Literal["Subject"] = "Subject"


class Dataset(SPARQLSerializable):
    hasSamples: Subject
    schemaKey: Literal["Dataset"] = "Dataset"

    def to_sparql(self, var_name="?dataset_uuid") -> str:
        subject_triples = self.hasSamples.to_sparql("?subject_uuid")
        subject_triples = "\n    ".join(subject_triples)
        # Always include these triple patterns
        dataset_triples = "\n    ".join(
            [
                f"{var_name} a nb:{self.schemaKey}.",
                f"{var_name} nb:hasLabel ?dataset_name.",
                f"{var_name} nb:hasSamples ?subject_uuid.",
                f"OPTIONAL {{{var_name} nb:hasPortalURI ?dataset_portal_uri.}}",
            ]
        )

        num_sessions_filter = ""
        if self.hasSamples.hasSession.min_num_imaging_sessions is not None:
            num_sessions_filter = "\n".join(
                [
                    f"GROUP BY {get_select_variables(SPARQL_SELECTED_VARS)}",
                    f"HAVING (COUNT(DISTINCT ?imaging_session) >= {self.hasSamples.hasSession.min_num_imaging_sessions})",
                ]
            )

        return f"""
SELECT {get_select_variables(SPARQL_SELECTED_VARS)}
WHERE {{
    {dataset_triples}
    {subject_triples}
}}
{num_sessions_filter}
""".strip()
