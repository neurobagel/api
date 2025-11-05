from typing import Literal

from pydantic import BaseModel
from pydantic.alias_generators import to_snake


def format_value(value):
    if isinstance(value, str):
        # TODO: Update to handle other prefixes as needed - might be dynamic based on the community
        if value.startswith(("nidm:", "np:")):
            return value
        return f'"{value}"'
    # TODO: Handle numeric values (e.g. for min/max age)


class SPARQLSerializable(BaseModel):
    def to_sparql(self, var_name: str) -> str:
        var_name = to_snake(var_name)
        triples = []
        schema_key = getattr(self, "schemaKey", None)
        if schema_key:
            triples.append(f"{var_name} a nb:{schema_key}.")

        for field in self.model_fields:
            value = getattr(self, field)
            if field == "schemaKey":
                continue

            predicate = f"nb:{field}"
            if isinstance(value, SPARQLSerializable):
                nested_var = f"?{to_snake(value.__class__.__name__)}"
                triples.append(f"{var_name} {predicate} {nested_var}.")
                triples.append(value.to_sparql(nested_var))
            else:
                if value is None:
                    continue
                formatted_value = format_value(value)
                triples.append(f"{var_name} {predicate} {formatted_value}.")
        return "\n    ".join(triples)


class Acquisition(SPARQLSerializable):
    hasContrastType: str | None


class Pipeline(SPARQLSerializable):
    hasPipelineVersion: str | None
    hasPipelineName: str | None


class ImagingSession(SPARQLSerializable):
    hasAcquisition: Acquisition | None
    hasCompletedPipeline: Pipeline | None
    schemaKey: Literal["ImagingSession"] = "ImagingSession"


class Subject(SPARQLSerializable):
    hasSession: ImagingSession | None
    schemaKey: Literal["Subject"] = "Subject"


class Dataset(SPARQLSerializable):
    hasSamples: Subject
    schemaKey: Literal["Dataset"] = "Dataset"
    min_num_imaging_sessions: int | None = None

    def to_sparql(self, var_name="?dataset_uuid") -> str:
        subject_triples = self.hasSamples.to_sparql("?subject")
        # Always include these triple patterns
        dataset_triples = "\n    ".join(
            [
                f"{var_name} a nb:{self.schemaKey}.",
                f"{var_name} nb:hasLabel ?dataset_name.",
                f"OPTIONAL {{{var_name} nb:hasPortalURI ?dataset_portal_uri.}}",
            ]
        )

        num_sessions_filter = ""
        if self.min_num_imaging_sessions:
            num_sessions_filter = f"HAVING (COUNT(DISTINCT ?imaging_session) >= {self.min_num_imaging_sessions})"

        return f"""
SELECT ?dataset_uuid ?dataset_name ?dataset_portal_uri ?subject
WHERE {{
    {dataset_triples}
    {subject_triples}
}}
GROUP BY ?dataset_uuid ?dataset_name ?dataset_portal_uri ?subject
{num_sessions_filter}
""".strip()
