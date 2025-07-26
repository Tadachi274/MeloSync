# Installation
## languages
Some tools for development needs runtime for programming language.
These tools only run in our local computers and don't in a production server.

Install Go.

https://go.dev/doc/install

## tools
First, Install [Task](https://taskfile.dev). It is a simple task runner.
This will help define utility commands.

```zsh
npm install -g @go-task/cli
```

You can install other tools using task. The `install-dev-tools` command installs all other tools.

```zsh
task install-dev-tools
```
