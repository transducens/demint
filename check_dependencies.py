import pkg_resources

# Read the list of dependencies from the file
with open('requirements.txt') as f:
    dependencies = [line.strip() for line in f if line.strip()]

# Get the list of installed packages
installed_packages = {pkg.key for pkg in pkg_resources.working_set}

# Check which dependencies are installed and which are not
installed = []
not_installed = []

for dependency in dependencies:
    if dependency.lower() in installed_packages:
        installed.append(dependency)
    else:
        not_installed.append(dependency)

# Print the results
print("Installed packages:")
for package in installed:
    print(f" - {package}")

print("\nNot installed packages:")
for package in not_installed:
    print(f" - {package}")

