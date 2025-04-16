import os
import toml
import os
import git
import re


def version_from_toml(file="pyproject.toml"):
    try:
        # Load the pyproject.toml file
        with open(file, "r") as f:
            pyproject_data = toml.load(f)

        # Extract the project info and version
        project_info = pyproject_data.get("project", {})
        version = project_info.get("version")

        if version:
            return version

        # Check if version is dynamically set
        if "tool.hatch.version" in pyproject_data:
            version_path = pyproject_data["tool.hatch.version"].get("path")
            if version_path and os.path.exists(version_path):
                with open(version_path, "r") as file:
                    for line in file:
                        if "__version__" in line:
                            # Extract the version from the line
                            version = line.split("=")[1].strip().strip('"').strip("'")
                            return version

        raise ValueError("Version not found in pyproject.toml")

    except Exception as e:
        print(f"Error: {e}")
        return None




def get_latest_tag():
    try:
        # Open the current repository
        repo = git.Repo(search_parent_directories=True)

        # Get the most recent tag
        tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)
        if tags:
            latest_tag = tags[-1].name
            return latest_tag
        else:
            raise ValueError("No tags found in the repository.")
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_version_from_tag(tag):
    # Assuming the tags follow a basic semantic versioning format: v1.0.0
    # Modify this function if your tag format differs
    pattern = r'v?(\d+\.\d+\.\d+)'  # Modify the regex pattern according to your version conventions
    match = re.match(pattern, tag)
    if match:
        return match.group(1)
    else:
        print(f"Tag {tag} does not match the version pattern.")
        return None

#from version import version_from_toml, get_latest_tag, get_version_from_tag
#version = version_from_toml("pyproject.toml")
#print(version)
#if not version:
#    tag = get_latest_tag()
#    version = get_version_from_tag(tag)
#print(version)