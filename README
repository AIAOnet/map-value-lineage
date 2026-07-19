# Value Lineage and Change-Impact Mapping

This project helps Codex understand how an entity value moves through an application, where it can change, and what may be affected by a code change.

The project contains three components:

## 1. Project agent instructions

The `AGENTS.md` file contains the instructions Codex follows before and after changing an application.

Place `AGENTS.md` in the root directory of the project or Codex project sandbox:

```text
<project-directory>\AGENTS.md
```

The instructions require Codex to:

- Read the latest entity graph before changing code.
- Understand the relevant values, methods, APIs, storage, events, and downstream effects.
- Perform impact analysis before implementation.
- Commit the application change first.
- Generate a new numbered graph version containing the application commit hash.
- Store the new graph under `entities_graphics`.

## 2. Codex skill

The `map-value-lineage` skill contains the reusable mapping workflow and JSON structure.

Copy the complete skill directory into the current user's Codex skills directory:

```text
C:\Users\<username>\.codex\skills\map-value-lineage\
```

The following file must exist directly inside that directory:

```text
C:\Users\<username>\.codex\skills\map-value-lineage\SKILL.md
```

Restart Codex or open a new task after installing the skill.

Invoke it with:

```text
Use $map-value-lineage to map <Entity>.<value> and analyze the impact of the requested change.
```

The skill produces:

```text
<entity>-<value>-vNNN.json
<entity>-<value>-vNNN.mmd
```

Save both files in the project's graph directory:

```text
<project-directory>\entities_graphics\<entity>\
```

Do not overwrite an older graph. Increment the version number for every new application change.

## 3. Mermaid graph viewer

The Mermaid graph viewer displays the generated `.mmd` graph files.

### Install

Run:

```text
setup.exe
```

### Start the viewer

After installation, run:

```text
run_viewer.exe
```

### Open a graph

1. Start `run_viewer.exe`.
2. Select or upload the required `.mmd` file.
3. Find generated graph files under:

```text
<project-directory>\entities_graphics\
```

If the project is running in a Codex sandbox, use the `entities_graphics` directory inside that sandbox instead.

## Expected workflow

```text
Install the Codex skill
-> place AGENTS.md in the project root
-> inspect the latest graph
-> analyze the requested change
-> update and test the application
-> commit the application change
-> generate the next JSON and Mermaid graph version
-> add the application commit hash to the JSON
-> save the files under entities_graphics
-> commit the new graph version
-> view the .mmd file with the Mermaid graph viewer
```

## Directory example

```text
project-root\
|-- AGENTS.md
|-- entities_graphics\
|   `-- order\
|       |-- order-status-v001.json
|       |-- order-status-v001.mmd
|       |-- order-status-v002.json
|       `-- order-status-v002.mmd
`-- application-files...

C:\Users\<username>\.codex\skills\
`-- map-value-lineage\
    |-- SKILL.md
    |-- agents\
    |-- assets\
    |-- references\
    `-- scripts\
```
