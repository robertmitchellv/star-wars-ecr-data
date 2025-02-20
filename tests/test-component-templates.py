from lxml import etree
from conftest import normalize_xml


def test_patient_template(jinja_env, patient_data, xml_nsmap, base_path):
    """Test that our template generates the expected patient XML structure."""
    # load and render the template
    template = jinja_env.get_template("components/patient.xml.j2")
    rendered_xml = template.render(
        patient=patient_data["components"]["patient"], nsmap=xml_nsmap
    )

    # load and extract the expected xml
    xml_path = base_path / "tests" / "assets" / "mon-mothma-covid-problem_eicr.xml"
    tree = etree.parse(str(xml_path))
    record_target = tree.find(".//{urn:hl7-org:v3}recordTarget")
    expected_xml = etree.tostring(record_target, encoding="unicode")

    # compare normalized versions
    normalized_rendered = normalize_xml(rendered_xml)
    normalized_expected = normalize_xml(expected_xml)

    # for debugging, print both versions if they don't match
    try:
        assert normalized_rendered == normalized_expected
    except AssertionError:
        print("\nNormalized Generated XML:")
        print(normalized_rendered)
        print("\nNormalized Expected XML:")
        print(normalized_expected)
        raise
