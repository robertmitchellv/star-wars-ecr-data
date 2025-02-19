from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# load the json data
data = {
    "patient": {
        "identifiers": {
            "medical_record": {
                "root": "2.16.840.1.113883.19.5",
                "extension": "PT-470123",
            },
            "ssn": {"extension": "555-55-5555"},
        },
        "name": {"use": "L", "given": "Kid", "family": "Karri"},
        "address": {
            "street": "2222 Home Street",
            "city": "Salt Lake City",
            "state": "UT",
            "zip": "84101",
            "county": "Salt Lake County",
            "country": "US",
        },
        "contact": {"phone": "555-555-2005", "email": "kkkidd@email.com"},
        "demographics": {
            "gender": {"code": "F", "displayName": "Female"},
            "birthDate": "20021027",
            "deceased": "false",
            "race": {"code": "2028-9", "displayName": "Asian"},
            "ethnicity": {"code": "2186-5", "displayName": "Not Hispanic or Latino"},
            "language": {"code": "en", "preferred": "true"},
        },
        "guardian": {
            "name": {"given": "Martha", "family": "Mum"},
            "address": {
                "street": "2222 Home Street",
                "city": "Salt Lake City",
                "state": "UT",
                "zip": "84101",
                "county": "Salt Lake County",
                "country": "US",
            },
            "contact": {"phone": "555-555-2005", "email": "mmmum@email.com"},
        },
    }
}

# set up the Jinja2 environment
env = Environment(
    loader=FileSystemLoader(
        Path(__file__).resolve().parent.parent / "assets" / "templates"
    )
)
template = env.get_template("components/shared/patient.xml.j2")

# render the template with the data
rendered_xml = template.render(patient=data["patient"])

# define the output directory and file path
output_dir = Path(__file__).resolve().parent.parent / "assets" / "test-output"
output_file_path = output_dir / "test-patient-output.xml"

# ensure the output directory exists
output_dir.mkdir(parents=True, exist_ok=True)

# save the output to a file
output_file_path.write_text(rendered_xml, encoding="utf-8")

print(f"Template rendered and saved to {output_file_path}")
