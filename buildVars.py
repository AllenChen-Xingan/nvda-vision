# -*- coding: UTF-8 -*-

# Build variables for NVDA Vision add-on

import os.path

# Add-on information variables
addon_info = {
	# Add-on Name/identifier, internal for NVDA
	"addon_name": "nvdaVision",

	# Add-on summary, usually the user visible name of the addon.
	"addon_summary": "NVDA Vision Screen Reader",

	# Add-on description
	"addon_description": "AI-powered screen reader using computer vision models to recognize and describe UI elements in inaccessible applications. Supports GPU/CPU models and cloud API fallback.",

	# version
	"addon_version": "1.0.0",

	# Author(s)
	"addon_author": "NVDA Vision Team <support@nvda-vision.org>",

	# URL for the add-on documentation support
	"addon_url": "https://github.com/nvda-vision/nvda-vision",

	# Documentation file name
	"addon_docFileName": "readme.html",

	# Minimum NVDA version supported (e.g. "2018.3.0", minor version is optional)
	"addon_minimumNVDAVersion": "2023.1.0",

	# Last NVDA version supported/tested (e.g. "2018.4.0", ideally more recent than minimum version)
	"addon_lastTestedNVDAVersion": "2024.4.0",

	# Add-on update channel (default is None, denoting stable releases)
	"addon_updateChannel": None,
}

# Define the python files that are the sources of your add-on.
# You can use glob expressions here, they will be expanded.
pythonSources = [
	os.path.join("addon", "globalPlugins", "nvdaVision", "*.py"),
	os.path.join("addon", "globalPlugins", "nvdaVision", "**", "*.py"),
]

# Files that contain strings for translation.
# Usually your python sources, the manifest file and the readme.
i18nSources = pythonSources + ["manifest.ini"]

# Files that will be ignored when building the package.
# Typically, these are files that are not needed in the final package.
excludedFiles = [
	"*.pyc",
	"*.pyo",
	"*.log",
	"__pycache__",
	".git*",
	".DS_Store",
	"*.md",
	"tests",
	"*.spec.md",
]
