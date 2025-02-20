import json
import pytest
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from lxml import etree
import re


@pytest.fixture
def jinja_env():
    """Shared Jinja environment fixture."""
    return Environment(
        loader=FileSystemLoader(
            Path(__file__).resolve().parent.parent / "assets" / "templates"
        )
    )


@pytest.fixture
def base_path():
    """Shared base path fixture."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def cda_nsmap():
    """Standard CDA namespace mapping."""
    return {
        "cda": "urn:hl7-org:v3",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "sdtc": "urn:hl7-org:sdtc",
        "voc": "http://www.lantanagroup.com/voc",
    }


@pytest.fixture
def xml_nsmap():
    """Namespace mapping for XML generation (with default namespace)."""
    return {
        None: "urn:hl7-org:v3",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "sdtc": "urn:hl7-org:sdtc",
        "voc": "http://www.lantanagroup.com/voc",
    }


@pytest.fixture
def patient_data(base_path):
    """Load the Mon Mothma COVID test data from JSON."""
    json_path = base_path / "assets" / "mappings" / "mon-mothma-covid.json"
    with open(json_path) as f:
        return json.load(f)


def clean_xml_string(xml_string: str) -> str:
    """
    Clean an XML string by:
    1. Removing comments
    2. Removing empty lines
    3. Removing leading/trailing whitespace
    4. Normalizing whitespace between attributes
    """
    # remove xml comments
    xml_string = re.sub(r"<!--.*?-->\n?\s*", "", xml_string, flags=re.DOTALL)

    # remove empty lines and normalize whitespace
    lines = [line.strip() for line in xml_string.split("\n") if line.strip()]
    return "\n".join(lines)


def normalize_xml(xml_string: str, strip_ns: bool = True) -> str:
    """
    Normalize XML string for comparison by:
    1. Parsing and re-serializing
    2. Optionally removing namespaces
    3. Removing comments
    4. Sorting attributes
    """
    parser = etree.XMLParser(remove_blank_text=True, remove_comments=True)

    # parse xml
    try:
        root = etree.fromstring(xml_string.encode(), parser)
    except etree.XMLSyntaxError as e:
        print(f"XML parsing error: {e}")
        print(f"Problematic XML:\n{xml_string}")
        raise

    if strip_ns:
        # remove namespace declarations
        for elem in root.getiterator():
            if isinstance(elem.tag, str):
                if "}" in elem.tag:
                    elem.tag = elem.tag.split("}", 1)[1]
            # sort and normalize attributes
            if elem.attrib:
                # convert attributes to sorted list of tuples
                attrs = sorted(elem.attrib.items())
                # clear existing attributes
                elem.attrib.clear()
                # add back in sorted order
                for key, value in attrs:
                    if "}" in key:
                        key = key.split("}", 1)[1]
                    elem.attrib[key] = value

        # remove all namespace declarations
        etree.cleanup_namespaces(root)

    # convert back to string and clean
    xml_string = etree.tostring(root, pretty_print=True, encoding="unicode")
    return clean_xml_string(xml_string)


def strip_namespaces(xml_string: str) -> str:
    """Alias for normalize_xml with strip_ns=True for backwards compatibility."""
    return normalize_xml(xml_string, strip_ns=True)
