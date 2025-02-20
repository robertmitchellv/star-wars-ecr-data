from saxonche import PySaxonProcessor
from pathlib import Path

# define the base directory and file paths
base_dir = Path(__file__).parent
stylesheet_path = base_dir / "schxslt" / "pipeline-for-svrl.xsl"
schematron_path = base_dir / "CDAR2_IG_PHCASERPT_R2_STU1.1_SCHEMATRON.sch"
output_path = base_dir / "CDAR2_IG_PHCASERPT_R2_STU1.1_SCHEMATRON.xsl"

# create an instance of the processor
saxon_processor = PySaxonProcessor(license=False)

# use the processor within a context to ensure proper resource management
with saxon_processor as processor:
    xslt_processor = processor.new_xslt30_processor()

    # compile the XSLT stylesheet using the stylesheet_file keyword
    try:
        compiled_stylesheet = xslt_processor.compile_stylesheet(
            stylesheet_file=str(stylesheet_path)
        )
        print("Stylesheet compiled successfully.")
    except Exception as e:
        print("Error during stylesheet compilation:", str(e))
        compiled_stylesheet = None

    # check if the stylesheet was compiled
    if compiled_stylesheet is None:
        print("Failed to compile stylesheet. Check the file path and permissions.")
    else:
        # perform the transformation using the compiled stylesheet
        try:
            # we must use the compiled stylesheet directly for the transformation
            result = compiled_stylesheet.transform_to_string(
                source_file=str(schematron_path)
            )
            if result:
                print("Transformation successful, writing output to file...")
                with open(output_path, "w") as file:
                    file.write(result)
            else:
                print("No output was generated from the transofrmation.")
        except Exception as e:
            print("Error during transformation:", str(e))
