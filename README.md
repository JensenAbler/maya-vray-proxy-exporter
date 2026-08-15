# Maya V-Ray proxy exporter

Copy the complete contents of `vray_proxy_shelf_tool.py` into a Maya Python
Script Editor tab, select the code, and drag it onto a shelf.

The script shows a filename field with a **Browse** button for choosing an
existing `.vrmesh` to overwrite, then exports the current selection to
`<current Maya project>/assets`. It creates a proxy node and writes a same-named
material-rules `.xml` beside it.

Reference: https://documentation.chaos.com/space/VMAYA/111741412/vrayCreateProxy
