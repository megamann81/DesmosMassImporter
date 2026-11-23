# Desmos 3D Triangle Loader

Bulk-load thousands of `triangle(...)` lines into the **Desmos 3D Calculator** in one step,
straight from `.txt` files on your computer.

Pasting many `triangle((x,y,z),(x,y,z),(x,y,z))` lines into Desmos by hand tends not to turn
them into triangles (the pasted text is parsed differently from typed text), and driving the
page one expression at a time is slow. This loader skips both: it reads your files in the
browser, builds the expressions in Desmos's own internal format, and hands them over in a single
`setState` call.

Everything runs locally in your browser. Nothing is uploaded anywhere.

> **Authorship:** **megamann81** generated and reviewed the code, with **Claude** (an AI model made by
> Anthropic) writing all of the code. See [Authorship and license](#authorship-and-license).

---

## Files

| File | What it is |
|---|---|
| `desmos_3d_triangle_loader.js` | The loader. Paste it into the browser console on desmos.com/3d. |
| `triangles_all.txt` | Example data: 7,500 triangles (a head), all 15 original folders merged. |
| `mesh_to_triangles.py` | Optional. Converts a `.glb` / `.obj` / `.stl` mesh into `triangle(...)` lines. |
| `glb_to_obj.py` | Helper used by `mesh_to_triangles.py` (GLB reader + mesh decimator). Keep it next to that script. |
| `LICENSE` | MIT license text. |

---

## Quick start

1. Unzip your triangle files so they sit in a normal folder (the loader cannot read inside a `.zip`).
2. Open **https://www.desmos.com/3d** in Chrome, Edge or Firefox.
3. Press **F12** and open the **Console** tab.
4. Open `desmos_3d_triangle_loader.js`, copy **all** of it, paste it into the console, press **Enter**.
   - Chrome may refuse the first paste. Type `allow pasting`, press Enter, then paste again.
5. The console prints `Loader ready…`. A blue **Load triangle folder** button appears at the **top centre**
   of the page.
6. Click it and pick the folder that contains your `.txt` files. Picking a parent folder works:
   every `.txt` inside it (including subfolders) is read, in natural order (`Folder_2` before `Folder_10`).
7. Wait a moment. The button shows `Loading N triangles…`, the console prints
   `Loaded N triangles from X file(s) into Y folder(s)`, and the button removes itself.

**Undo:** `Ctrl+Z` removes the whole import in one step.

To load more files later, paste the script again (it replaces any old button).

---

## Input format

One triangle per line, three 3D points:

```
triangle((x1,y1,z1),(x2,y2,z2),(x3,y3,z3))
```

- Only files ending in `.txt` are read. Other files in the folder are ignored.
- Spaces and Windows (CRLF) line endings are fine. Lines that don't match the pattern are skipped silently,
  so check the loaded count in the console against what you expect.
- Use plain decimals such as `0.125` or `-3`. **Avoid scientific notation** (`1e-5`): Desmos reads
  `e` as Euler's number.
- The 3D calculator's `triangle` takes exactly three points. There is no 3D `polygon`.

---

## Options

Edit the constants at the top of the script before pasting:

| Constant | Default | Meaning |
|---|---|---|
| `COLOR` | `'#c98f6b'` | One colour for every triangle. Desmos 3D adds its own lighting, so a single colour still shows form. |
| `COLLAPSE_FOLDERS` | `true` | Create folders collapsed. Keep this on: expanding thousands of rows in the expression list is slow. |
| `SINGLE_FOLDER` | `true` | `true`: everything goes into one folder called **All triangles**. `false`: one Desmos folder per `.txt` file, named after its parent directory (or the file name if there is none). |
| `Z_UP` | `false` | Desmos 3D is **z-up**. Most scans and GLB/OBJ models are **y-up**, so they show up lying on their side. Set `true` to remap `(x, y, z) → (x, −z, y)`. That is a rotation (no mirroring). Leave `false` for z-up data (STL/CAD, Blender, most maths data). |

---

## Making triangle files from a 3D model

`mesh_to_triangles.py` turns a mesh into loader-ready lines. It needs Python 3 and `numpy`.

```
python mesh_to_triangles.py model.glb --faces 3000 -o triangles_all.txt
python mesh_to_triangles.py model.obj --faces 2000 --z-up
python mesh_to_triangles.py model.glb --faces 7500 --folders triangle_folders
```

| Option | Meaning |
|---|---|
| `--faces N` | Target triangle count (default 3000). The mesh is simplified with quadric-error decimation. |
| `--size S` | Scale so the longest side is `S` units (default 2.0; `0` keeps the original units). The model is also centred on the origin. |
| `--z-up` | Bake the y-up → z-up remap into the file (same maths as the loader's `Z_UP`). Use **one or the other**, not both. |
| `-o FILE` | Output file (default `triangles_all.txt`). |
| `--folders DIR` | Also write `DIR/Folder_01/triangles_01.txt`, … with 500 triangles each. |

Supported inputs: `.glb`, `.obj`, `.stl` (ASCII or binary). For FBX, USDZ or 3MF, export GLB or OBJ from
your 3D tool first. Textures and colours are not carried over; only geometry is.

Proprietary files (for example Meshy's `.meshy` container) can't be read. Re-export the model as GLB/OBJ/STL.

---

## How it works

1. Finds the calculator object (`window.Calc`, or any global exposing `getState` and `setState`).
2. Reads each `.txt` with the browser's `File` API and extracts every triangle with a regular expression.
3. Takes `Calc.getState()`, appends one folder plus one expression per triangle:
   `\operatorname{triangle}\left(\left(x,y,z\right),\left(…\right),\left(…\right)\right)`, each with `COLOR`.
4. Calls `Calc.setState(state, { allowUndo: true })` once.
5. A few seconds later it logs how many expressions Desmos flagged as errors (best-effort check).

Using `getState` → modify → `setState` keeps your existing 3D view and settings and anything already on the graph.

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Nothing printed, no button | The paste was blocked or truncated. Type `allow pasting` in the console and paste again; make sure you copied the whole file. Check the Console tab (not Elements) for a red error. |
| Button says *Calculator object not found* | You're not on desmos.com/3d, or Desmos exposes the calculator under a different name. Run `Object.keys(window).filter(k => /calc|desmos/i.test(k))` and look for the right name. |
| Button says *No .txt files in that selection* | Pick the folder that holds the `.txt` files (or a parent of it), not an individual file or a `.zip`. |
| Loaded count is lower than expected | Some lines didn't match the format (see **Input format**). Open the file and look for stray text or scientific notation. |
| Loaded, but nothing is drawn, or the console reports errors | The `\operatorname{triangle}` spelling may differ in your Desmos version. Type one triangle by hand, then run `Calc.getState().expressions.list.at(-1).latex` and compare it with the loader's `latex` function. |
| Model is lying on its side or upside down | y-up vs z-up. Set `Z_UP = true`, or convert with `--z-up`. |
| Model is tiny or huge | Zoom in the viewer, or rescale with `mesh_to_triangles.py --size`. |
| Page is slow or freezes | Too many expressions. Aim for a few thousand triangles at most; reduce with `--faces`, or load files in batches by picking one subfolder at a time. Keep folders collapsed. |
| Picker doesn't open | Click the blue button yourself (browsers only allow the file dialog from a real click). |

---

## Limits and notes

- **Not yet confirmed in a live Desmos session.** The loader was tested in Node against the real data
  (parsing, ordering, folder structure, ids, round-trip of every number) with a mock of the calculator object.
  If your Desmos build behaves differently, the troubleshooting table lists what to check first.
- Desmos 3D wasn't designed for dense meshes: thousands of triangles work, tens of thousands will not.
- One colour for all triangles; no textures, vertex colours or per-triangle shading controls.
- The script only **adds** to the graph. Remove a previous import with `Ctrl+Z` or by deleting the folder.
- Desmos may change its page or API at any time; this is an unofficial helper, not a Desmos feature.

---

## Authorship and license

**Project generated and reviewed by megamann81; code written by Claude.** The loader
(`desmos_3d_triangle_loader.js`), `mesh_to_triangles.py`, and `glb_to_obj.py` were written entirely by
Claude, an AI model made by Anthropic. **megamann81** generated the project and reviewed the code.
This README documents the project and its use.

**License: MIT.** You may use, copy, modify, publish and distribute this software, including commercially,
provided the copyright notice and licence text in [`LICENSE`](LICENSE) stay with it. It comes with no warranty.
Replace `[YOUR NAME]` in `LICENSE` with the name (or handle) you want shown as copyright holder.
If you would rather waive all rights, swap in the CC0 or Unlicense text instead.

Scope and caveats:
- The licence covers only the four files listed above. It does **not** cover the separate Desmos importer package
  (`Desmos-3D-Model-Importer-Rebuilt-*`), which builds on a third-party project with its own terms.
- Models and data you convert keep whatever licence or terms they came with (for example a service's
  terms of use). Check them before publishing the results.
- This is an unofficial helper. It is not made by, affiliated with, or endorsed by Desmos or Meshy.
- Whether AI-written code can be copyrighted, and by whom, is unsettled in many places. MIT is still a sound way
  to tell others what they may do with it, but this is not legal advice.
