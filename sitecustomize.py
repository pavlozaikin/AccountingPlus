from accountingplus.weasyprint_support import bootstrap


# Ensure Homebrew-installed libraries are visible to dynamic loaders.
# Python automatically imports this module on startup when it is present
# on the import path (see the standard `site` module documentation).
bootstrap()
