from collections import namedtuple

# For the request
DOG_ROOT = "http://206.12.99.17"
DOG_DB = "parkinson_data"
DOG_PORT = 5820
QUERY_URL = f"{DOG_ROOT}:{DOG_PORT}/{DOG_DB}/query"
QUERY_HEADER = {
    "Content-Type": "application/sparql-query",
    "Accept": "application/sparql-results+json",
}

# For the SPARQL query
DEFAULT_CONTEXT = """
PREFIX bg: <http://neurobagel.org/vocab/>
PREFIX snomed: <http://neurobagel.org/snomed/>
PREFIX nidm: <http://purl.org/nidash/nidm#>
"""

# Store domains in named tuples
Domain = namedtuple("Domain", ["var", "pred"])
# Core domains
AGE = Domain("age", "bg:hasAge")
SEX = Domain("sex", "bg:sex")
DIAGNOSIS = Domain("diagnosis", "bg:diagnosis")
IMAGE_MODAL = Domain("image_modal", "bg:hasContrastType")
TOOL = Domain("tool", "")
PROJECT = Domain("project", "bg:hasSamples")
CONTROL = Domain("nidm:Control", "nidm:isSubjectGroup")

CATEGORICAL_DOMAINS = [SEX, DIAGNOSIS, IMAGE_MODAL]
