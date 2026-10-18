# Director

**Teste integrado da cozinha:** [resultado, correções pontuais e limites](docs/teste-cozinha-2026-10-17/README.md). Hermes criou uma cozinha anexa e ampliou a mesa; o teste revelou e corrigiu o envelope de marcadores do editor e a exigência indevida de simulação dinâmica da mesa fixa. 100 testes Director e 11 da guarda passaram; as pendências maiores continuam abertas.

**Builds and edits functional 3D scenes in Unreal Engine through conversation, with a small or local LLM planning, composing operations, inspecting the result and investigating alternatives.**

The LLM (or a person) writes a *ficha*: a short JSON with an operation and a few fields ("create a 4 × 4 m room", "move the door to the opposite wall"). A deterministic core, with no LLM inside, validates it, plans the smallest change, asks Unreal to do it with Unreal's own automation, measures the result and saves. If anything fails, the scene goes back to what it was.

> **Director is the successor of [unreal-local-director](https://github.com/talisp/unreal-local-director), now called "Antigo Director" (Old Director), which is discontinued.** An explanation of why will come later.

## Status: early, first delivery only

**Histórico e próximos passos:** [entrega, evidências publicadas e pendências de 17/10/2026](docs/evolucao-2026-10-17/README.md). Inclui o ensaio real do Qwen, resultados negativos de navegação, fichas de referência e issues para a evolução seguinte.

**17 Oct 2026 — agent interface:** `python -m director --help` lists the commands without connecting to Unreal. `observar CENA [ID ...]` separates the desired plan from measured actor bounds, `medir CENA CONSULTAS.json` exposes native collision/navigation queries, and `assets TERMO ...` searches assets already in `/Game`. Creating a new scene is automatic through `fazer`. JSON output is compact ASCII to avoid corrupted accents in Windows terminal transports.

Navigation readiness now checks the engine's loading/build lock as well as build activity. It is reported separately from connectivity: only a complete path query validates a specific route. No changes to the construction representation or rollback mechanism are required by this increment.

Verified on 17 Oct: 49 core/interface tests and 4 Hermes guard tests passed. Native queries measured a 150 cm corridor, a clear capsule sweep, a blocking wall and a complete route after rebuilding navigation. Reopening that scene could leave navigation without a usable route until a native rebuild; a separate north–south doorway case still returned a partial path. These navigation issues are not claimed fixed. The original lab scene was restored and its actor inventory preserved. The new interface has not yet been benchmarked in a fresh end-to-end Qwen run.

Measured on 13 Oct 2026, Unreal Engine 5.8.3, in a separate lab project ([numbers](docs/entrega1/README.md)):

| Request | What happened in Unreal |
|---|---|
| "Create a 4 × 4 m room with a door, a window and a table." | 9 parts created; inner size measured by ray: 400.0 × 400.0 cm |
| "Make the room 5 × 4 m and move the door to the opposite wall." | 7 parts updated, none deleted or recreated; a table moved by hand stayed where the person left it |
| "Put a plate and a glass on the table." | 2 physical objects; with physics running they stayed on the table |

Also measured: the door blocks when closed and frees the way when open; an Unreal `Character` walks in through the open door; save, close the editor and reopen keeps everything; what moved during Play can be written back to the saved scene; an invalid request is refused before touching the scene; a failure in the middle is rolled back. 64 of 64 checks in the final run, 33 of 33 tests without Unreal.

**First contact with a local LLM (14 Oct 2026):** a local Qwen, through Hermes Agent, operated the Director in a first test and a real conversation. It built a room from one sentence correctly, but also made errors (ignored parts of a request, invented a size, changed the scene after being criticized). What happened and what changed is in [`hermes/README.md`](hermes/README.md). Not measured yet.

**Changes on 14 Oct 2026** (after the first contact with the local LLM):
- **Rooms of any size** (fixes [#1](https://github.com/talisp/Director/issues/1)): the 2–20 m limit was removed; a room only needs sizes above zero (a 1 × 3 m corridor and a 0.6 × 0.5 m closet were built in Unreal).
- **Rooms side by side share one wall** (fixes [#2](https://github.com/talisp/Director/issues/2)): placed 0.15 m apart (one wall), two rooms get a single 15 cm wall instead of two, and a door in it is the passage from one room to the other. A door or window that would open against another wall is refused. Tested without Unreal (53 tests; existing scenes unchanged); **not yet built in Unreal**.
- **Historical approval policy** ([#3](https://github.com/talisp/Director/issues/3), superseded on 16 Oct): the experimental Hermes profile now executes authorized tasks without a card per command. `director-guarda` only repairs malformed clarification arguments; the former directory restriction was removed.
- **Questions reach the person** (fixes [#5](https://github.com/talisp/Director/issues/5)): the same plugin repairs the question list when the model sends it as text (with a stray `}` or a missing `]`); the 15 questions recorded in real conversations pass Hermes' own validation.
- Operator rules: discussion alone does not authorize scene changes; an execution request authorizes its necessary operations. Experiments are allowed in the lab, with evidence before adopting new permanent solutions.

**Not there yet:** a measured LLM filling the fichas reliably; characters with a body and animation; real-looking parts (everything is cubes and cylinders); Smart Objects; sequences, camera and video; an opening without a door between rooms.

> The numbers above are from the run of 13 Oct 2026, 20:10, made before the package was renamed from `director2` to `director`. After the rename the whole run was repeated on a new scene (22:52): 64 of 64 again, and 33 of 33 tests without Unreal (53 since the changes of 14 Oct).

## Try it

Needs Python 3.11+ (standard library only). Without Unreal:

```
python -m unittest director.testes.testes_nucleo
python -m director capacidades
```

With Unreal Engine 5.8 installed (creates and opens a small lab project; it never talks to another project):

```
python -m director.lab criar
python -m director.lab abrir
python -m director pecas
python -m director fazer sala director/fichas/comando1.json
```

## Where things are

| Path | What |
|---|---|
| `director/nucleo/` | the core: operations and refusals, the scene plan (*planta*), minimal-change planner, executor with rollback |
| `director/nucleo/pecas.py` | the parts: each one is a Blueprint with a Construction Script, created by the program |
| `director/editor/` | what runs inside the Unreal editor |
| `director/ponte.py`, `director/lab.py` | protections and the lab project |
| `director/fichas/` | the three example requests |
| [`hermes/`](hermes/README.md) | instructions for a local LLM operating the Director through Hermes Agent (rules, skill, profile installer), and what the first test showed |
| [`docs/CONHECIMENTO.md`](docs/CONHECIMENTO.md) | what is reusable, which Epic APIs are used, pitfalls already measured, what is verified, provisional or only a hypothesis, and how to resume |

Code comments and documents are in Portuguese.

## References and credits

Director borrows ideas, thresholds and, where an issue says so, adapted code from these research projects. Thanks to their authors.

- **[SceneSmith](https://github.com/nepfaff/scenesmith)** — *SceneSmith: Agentic Generation of Simulation-Ready Indoor Scenes* ([arXiv 2602.09153](https://arxiv.org/abs/2602.09153), ICML 2026), MIT and Toyota Research Institute. Code under the MIT License. Used for:
  - door and window clearance zones and the 2D reachability check ([#29](https://github.com/talisp/Director/issues/29));
  - the text floor plan for a model without vision ([#30](https://github.com/talisp/Director/issues/30));
  - scored review with bounded rounds ([#31](https://github.com/talisp/Director/issues/31));
  - physics thresholds ([#25](https://github.com/talisp/Director/issues/25));
  - mass from size and material ([#13](https://github.com/talisp/Director/issues/13));
  - size-ranked asset retrieval ([#27](https://github.com/talisp/Director/issues/27)).

  Director does not use its multi-agent orchestration, its Drake simulation or its 3D generation.
- **[SpatialGen](https://github.com/manycore-research/SpatialGen)** — *SpatialGen: Layout-guided 3D Indoor Scene Generation* (3DV 2026), HKUST Spatial AI Lab and Manycore Tech. Code under the MIT License; its model weights have their own licenses (the FLUX LoRA is non-commercial). Studied as a reference for appearance generated from a layout, together with its sibling [SpatialLM](https://github.com/manycore-research/SpatialLM) (point cloud to structured walls, doors, windows and boxes). Not used in the code yet.

Code adapted from an MIT project keeps its copyright notice and license text in a third-party notices file.

## License

Source-available, not open source. See [LICENSE](LICENSE).
