#!/bin/bash

# Define the path to the pre-commit hook
HOOK_PATH=".git/hooks/pre-commit"

echo "Installing pre-commit hook..."

# Create the hooks directory if it doesn't exist
mkdir -p .git/hooks

# Write the pre-commit hook script
cat << 'EOF' > "$HOOK_PATH"
#!/bin/bash

echo "Running ruff check before commit..."
ruff check .

if [ $? -ne 0 ]; then
  echo "Ruff check failed. Please fix the errors before committing." >&2
  exit 1
fi

echo "Ruff check passed."

echo "Running pytest before commit..."
pytest --ignore=tests/test_build.py --ignore=tests/test_pypi_package.py --ignore=tests/test_end_to_end.py

if [ $? -ne 0 ]; then
  echo "Pytest failed. Please fix the errors before committing." >&2
  exit 1
fi

echo "Pytest passed."
exit 0
EOF

# Make the hook executable
chmod +x "$HOOK_PATH"

echo "Pre-commit hook installed successfully!"
echo "Ruff check and Pytest will now run automatically before each commit."