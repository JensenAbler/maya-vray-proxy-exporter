# Maya V-Ray proxy exporter

Copy the complete contents of `vray_proxy_shelf_tool.py` into a Maya Python
Script Editor tab, select the code, and drag it onto a shelf.

The script shows a filename field with a **Browse** button for choosing an
existing `.vrmesh` to overwrite, then exports the current selection to
`<current Maya project>/assets` without replacing the original geometry. It
loads the exported file as a new proxy, applies shader overrides using the
materials assigned to the original selection, validates those materials against
the proxy's embedded shader-set names, and writes the completed rules to a
same-named `.xml` beside the proxy file. The created proxy is named after the
`.vrmesh` filename with a `_proxy` suffix.

Reference: https://documentation.chaos.com/space/VMAYA/111741412/vrayCreateProxy
