import gpxpy


# Returns content of a File (NOT FileField) From Django for runners  https://github.com/jedie/django-for-runners/
def parse_gpx_file(filepath):
    assert filepath.is_file(), f"File not found: '{filepath}'"
    with filepath.open("r") as f:
        content = f.read()
    return gpxpy.parse(content)
