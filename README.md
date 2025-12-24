# privacy-query-engine

<div align="center">

[![Build status](https://github.com/curleaf/privacy-query-engine/workflows/build/badge.svg?branch=master&event=push)](https://github.com/curleaf/privacy-query-engine/actions?query=workflow%3Abuild)
[![Python Version](https://img.shields.io/pypi/pyversions/privacy-query-engine.svg)](https://pypi.org/project/privacy-query-engine/)
[![Dependencies Status](https://img.shields.io/badge/dependencies-up%20to%20date-brightgreen.svg)](https://github.com/curleaf/privacy-query-engine/pulls?utf8=%E2%9C%93&q=is%3Apr%20author%3Aapp%2Fdependabot)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Security: bandit](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/curleaf/privacy-query-engine/blob/master/.pre-commit-config.yaml)
[![Semantic Versions](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--versions-e10079.svg)](https://github.com/curleaf/privacy-query-engine/releases)
[![License](https://img.shields.io/github/license/curleaf/privacy-query-engine)](https://github.com/curleaf/privacy-query-engine/blob/master/LICENSE)
![Coverage Report](assets/images/coverage.svg)

A Python SDK for differential privacy and de-identification in SQL queries

</div>

## Very first steps

### Initialize your code

1. Initialize `git` inside your repo:

```bash
cd privacy-query-engine && git init
```

2. If you don't have `Poetry` installed run:

```bash
make poetry-download
```

3. Initialize poetry and install `pre-commit` hooks:

```bash
make install
make pre-commit-install
```

4. Run the codestyle:

```bash
make codestyle
```

5. Upload initial code to GitHub:

```bash
git add .
git commit -m ":tada: Initial commit"
git branch -M main
git remote add origin https://github.com/curleaf/privacy-query-engine.git
git push -u origin main
```

### Set up bots

- Set up [Dependabot](https://docs.github.com/en/github/administering-a-repository/enabling-and-disabling-version-updates#enabling-github-dependabot-version-updates) to ensure you have the latest dependencies.
- Set up [Stale bot](https://github.com/apps/stale) for automatic issue closing.

### Poetry

Want to know more about Poetry? Check [its documentation](https://python-poetry.org/docs/).

<details>
<summary>Details about Poetry</summary>
<p>

Poetry's [commands](https://python-poetry.org/docs/cli/#commands) are very intuitive and easy to learn, like:

- `poetry add numpy@latest`
- `poetry run pytest`
- `poetry publish --build`

etc
</p>
</details>

### Building and releasing your package

Building a new version of the application contains steps:

- Bump the version of your package `poetry version <version>`. You can pass the new version explicitly, or a rule such as `major`, `minor`, or `patch`. For more details, refer to the [Semantic Versions](https://semver.org/) standard.
- Make a commit to `GitHub`.
- Create a `GitHub release`.
- And... publish 🙂 `poetry publish --build`

## 🎯 What's next

Well, that's up to you 💪🏻. I can only recommend the packages and articles that helped me.

- [`Typer`](https://github.com/tiangolo/typer) is great for creating CLI applications.
- [`Rich`](https://github.com/willmcgugan/rich) makes it easy to add beautiful formatting in the terminal.
- [`Pydantic`](https://github.com/samuelcolvin/pydantic/) – data validation and settings management using Python type hinting.
- [`Loguru`](https://github.com/Delgan/loguru) makes logging (stupidly) simple.
- [`tqdm`](https://github.com/tqdm/tqdm) – fast, extensible progress bar for Python and CLI.
- [`IceCream`](https://github.com/gruns/icecream) is a little library for sweet and creamy debugging.
- [`orjson`](https://github.com/ijl/orjson) – ultra fast JSON parsing library.
- [`Returns`](https://github.com/dry-python/returns) makes you function's output meaningful, typed, and safe!
- [`Hydra`](https://github.com/facebookresearch/hydra) is a framework for elegantly configuring complex applications.
- [`FastAPI`](https://github.com/tiangolo/fastapi) is a type-driven asynchronous web framework.

Articles:

- [Open Source Guides](https://opensource.guide/).
- [A handy guide to financial support for open source](https://github.com/nayafia/lemonade-stand)
- [GitHub Actions Documentation](https://help.github.com/en/actions).
- Maybe you would like to add [gitmoji](https://gitmoji.carloscuesta.me/) to commit names. This is really funny. 😄

## 🚀 Features

### Development features

- Supports for `Python 3.9` and higher.
- [`Poetry`](https://python-poetry.org/) as the dependencies manager. See configuration in [`pyproject.toml`](https://github.com/curleaf/privacy-query-engine/blob/master/pyproject.toml) and [`setup.cfg`](https://github.com/curleaf/privacy-query-engine/blob/master/setup.cfg).
- Automatic codestyle with [`black`](https://github.com/psf/black), [`isort`](https://github.com/timothycrosley/isort) and [`pyupgrade`](https://github.com/asottile/pyupgrade).
- Ready-to-use [`pre-commit`](https://pre-commit.com/) hooks with code-formatting.
- Type checks with [`mypy`](https://mypy.readthedocs.io); docstring checks with [`darglint`](https://github.com/terrencepreilly/darglint); security checks with [`safety`](https://github.com/pyupio/safety) and [`bandit`](https://github.com/PyCQA/bandit)
- Testing with [`pytest`](https://docs.pytest.org/en/latest/).
- Ready-to-use [`.editorconfig`](https://github.com/curleaf/privacy-query-engine/blob/master/.editorconfig), [`.dockerignore`](https://github.com/curleaf/privacy-query-engine/blob/master/.dockerignore), and [`.gitignore`](https://github.com/curleaf/privacy-query-engine/blob/master/.gitignore). You don't have to worry about those things.

### Deployment features

- `GitHub` integration: issue and pr templates.
- `Github Actions` with predefined [build workflow](https://github.com/curleaf/privacy-query-engine/blob/master/.github/workflows/build.yml) as the default CI/CD.
- Everything is already set up for security checks, codestyle checks, code formatting, testing, linting, docker builds, etc with [`Makefile`](https://github.com/curleaf/privacy-query-engine/blob/master/Makefile#L89). More details in [makefile-usage](#makefile-usage).
- [Dockerfile](https://github.com/curleaf/privacy-query-engine/blob/master/docker/Dockerfile) for your package.
- Always up-to-date dependencies with [`@dependabot`](https://dependabot.com/). You will only [enable it](https://docs.github.com/en/github/administering-a-repository/enabling-and-disabling-version-updates#enabling-github-dependabot-version-updates).
- Automatic drafts of new releases with [`Release Drafter`](https://github.com/marketplace/actions/release-drafter). You may see the list of labels in [`release-drafter.yml`](https://github.com/curleaf/privacy-query-engine/blob/master/.github/release-drafter.yml). Works perfectly with [Semantic Versions](https://semver.org/) specification.

### Open source community features

- Ready-to-use [Pull Requests templates](https://github.com/curleaf/privacy-query-engine/blob/master/.github/PULL_REQUEST_TEMPLATE.md) and several [Issue templates](https://github.com/curleaf/privacy-query-engine/tree/master/.github/ISSUE_TEMPLATE).
- Files such as: `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md` are generated automatically.
- [`Stale bot`](https://github.com/apps/stale) that closes abandoned issues after a period of inactivity. (You will only [need to setup free plan](https://github.com/marketplace/stale)). Configuration is [here](https://github.com/curleaf/privacy-query-engine/blob/master/.github/.stale.yml).
- [Semantic Versions](https://semver.org/) specification with [`Release Drafter`](https://github.com/marketplace/actions/release-drafter).

## Installation

```bash
pip install -U privacy-query-engine
```

or install with `Poetry`

```bash
poetry add privacy-query-engine
```

Then you can run

```bash
privacy-query-engine --help
```

or with `Poetry`:

```bash
poetry run privacy-query-engine --help
```

### Makefile usage

[`Makefile`](https://github.com/curleaf/privacy-query-engine/blob/master/Makefile) contains a lot of functions for faster development.

<details>
<summary>1. Download and remove Poetry</summary>
<p>

To download and install Poetry run:

```bash
make poetry-download
```

To uninstall

```bash
make poetry-remove
```

</p>
</details>

<details>
<summary>2. Install all dependencies and pre-commit hooks</summary>
<p>

Install requirements:

```bash
make install
```

Pre-commit hooks coulb be installed after `git init` via

```bash
make pre-commit-install
```

</p>
</details>

<details>
<summary>3. Codestyle</summary>
<p>

Automatic formatting uses `pyupgrade`, `isort` and `black`.

```bash
make codestyle

# or use synonym
make formatting
```

Codestyle checks only, without rewriting files:

```bash
make check-codestyle
```

> Note: `check-codestyle` uses `isort`, `black` and `darglint` library

Update all dev libraries to the latest version using one comand

```bash
make update-dev-deps
```

</p>
</details>

<details>
<summary>4. Code security</summary>
<p>

```bash
make check-safety
```

This command launches `Poetry` integrity checks as well as identifies security issues with `Safety` and `Bandit`.

```bash
make check-safety
```

</p>
</details>

<details>
<summary>5. Type checks</summary>
<p>

Run `mypy` static type checker

```bash
make mypy
```

</p>
</details>

<details>
<summary>6. Tests with coverage badges</summary>
<p>

Run `pytest`

```bash
make test
```

</p>
</details>

<details>
<summary>7. All linters</summary>
<p>

Of course there is a command to ~~rule~~ run all linters in one:

```bash
make lint
```

the same as:

```bash
make test && make check-codestyle && make mypy && make check-safety
```

</p>
</details>

<details>
<summary>8. Docker</summary>
<p>

```bash
make docker-build
```

which is equivalent to:

```bash
make docker-build VERSION=latest
```

Remove docker image with

```bash
make docker-remove
```

More information [about docker](https://github.com/curleaf/privacy-query-engine/tree/master/docker).

</p>
</details>

<details>
<summary>9. Cleanup</summary>
<p>
Delete pycache files

```bash
make pycache-remove
```

Remove package build

```bash
make build-remove
```

Delete .DS_STORE files

```bash
make dsstore-remove
```

Remove .mypycache

```bash
make mypycache-remove
```

Or to remove all above run:

```bash
make cleanup
```

</p>
</details>

## 📈 Releases

You can see the list of available releases on the [GitHub Releases](https://github.com/curleaf/privacy-query-engine/releases) page.

We follow [Semantic Versions](https://semver.org/) specification.

We use [`Release Drafter`](https://github.com/marketplace/actions/release-drafter). As pull requests are merged, a draft release is kept up-to-date listing the changes, ready to publish when you’re ready. With the categories option, you can categorize pull requests in release notes using labels.

### List of labels and corresponding titles

|               **Label**               |  **Title in Releases**  |
| :-----------------------------------: | :---------------------: |
|       `enhancement`, `feature`        |       🚀 Features       |
| `bug`, `refactoring`, `bugfix`, `fix` | 🔧 Fixes & Refactoring  |
|       `build`, `ci`, `testing`        | 📦 Build System & CI/CD |
|              `breaking`               |   💥 Breaking Changes   |
|            `documentation`            |    📝 Documentation     |
|            `dependencies`             | ⬆️ Dependencies updates |

You can update it in [`release-drafter.yml`](https://github.com/curleaf/privacy-query-engine/blob/master/.github/release-drafter.yml).

GitHub creates the `bug`, `enhancement`, and `documentation` labels for you. Dependabot creates the `dependencies` label. Create the remaining labels on the Issues tab of your GitHub repository, when you need them.

## 🛡 License

[![License](https://img.shields.io/github/license/curleaf/privacy-query-engine)](https://github.com/curleaf/privacy-query-engine/blob/master/LICENSE)

This project is licensed under the terms of the `MIT` license. See [LICENSE](https://github.com/curleaf/privacy-query-engine/blob/master/LICENSE) for more details.

## 📃 Citation

```bibtex
@misc{privacy-query-engine,
  author = {privacy-query-engine},
  title = {A Python SDK for differential privacy and de-identification in SQL queries},
  year = {2025},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/curleaf/privacy-query-engine}}
}
```

## Credits [![🚀 Your next Python package needs a bleeding-edge project structure.](https://img.shields.io/badge/python--package--template-%F0%9F%9A%80-brightgreen)](https://github.com/TezRomacH/python-package-template)

This project was generated with [`python-package-template`](https://github.com/TezRomacH/python-package-template)


## 📚 OpenAPI 规范

Privacy Query Engine 提供完整的 OpenAPI 3.0+ 规范文档，支持自动生成客户端 SDK 和集成到各种 API 工具。

### 查看交互式文档

启动服务后，访问以下 URL 查看交互式 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 导出 OpenAPI 规范

使用命令行工具导出 OpenAPI 规范文件：

```bash
# 导出为 JSON 格式
python scripts/export_openapi.py --format json --output openapi.json

# 导出为 YAML 格式
python scripts/export_openapi.py --format yaml --output openapi.yaml

# 同时导出 JSON 和 YAML
python scripts/export_openapi.py --format both --output openapi
```

### 集成到 API 工具

#### Postman

1. 打开 Postman
2. 点击 **File > Import**
3. 选择导出的 `openapi.json` 或 `openapi.yaml` 文件
4. Postman 会自动创建完整的 API 集合

#### Insomnia

1. 打开 Insomnia
2. 点击 **Application > Preferences > Data > Import Data**
3. 选择导出的 OpenAPI 文件
4. 所有 API 端点将自动导入

### 生成客户端 SDK

使用 OpenAPI Generator 生成各种语言的客户端 SDK：

```bash
# 安装 OpenAPI Generator
npm install @openapitools/openapi-generator-cli -g

# 生成 Python 客户端
openapi-generator-cli generate \
  -i openapi.json \
  -g python \
  -o ./client-python

# 生成 TypeScript 客户端
openapi-generator-cli generate \
  -i openapi.json \
  -g typescript-axios \
  -o ./client-typescript

# 生成 Java 客户端
openapi-generator-cli generate \
  -i openapi.json \
  -g java \
  -o ./client-java
```

支持的语言包括：Python, TypeScript, Java, Go, Rust, C#, PHP, Ruby 等 50+ 种语言。

### OpenAPI 规范特性

我们的 OpenAPI 规范包含：

- ✅ 完整的端点定义和参数说明
- ✅ 详细的请求/响应模型和示例
- ✅ 标准化的错误响应格式
- ✅ 按功能分组的 API 标签
- ✅ 安全方案定义（API Key, Bearer Token）
- ✅ 服务器配置（开发、测试、生产环境）
- ✅ 外部文档链接

### 验证 OpenAPI 规范

使用 OpenAPI 验证工具检查规范的有效性：

```bash
# 安装验证工具
pip install openapi-spec-validator

# 验证规范
openapi-spec-validator openapi.json
```

### 编程方式使用

在 Python 代码中使用导出功能：

```python
from main.api.server import app
from main.api.export import OpenAPIExporter

# 创建导出器
exporter = OpenAPIExporter(app)

# 导出为 JSON
exporter.export_json("openapi.json")

# 导出为 YAML
exporter.export_yaml("openapi.yaml")

# 同时导出两种格式
exporter.export_both("openapi")

# 获取 schema 字典
schema = exporter.get_schema()
```

### API 版本管理

当前 API 版本：**v3.0.0**

所有 API 端点都包含版本前缀 `/api/v1`，确保向后兼容性。

### 更多资源

- [OpenAPI 规范官方文档](https://swagger.io/specification/)
- [OpenAPI Generator 文档](https://openapi-generator.tech/)
- [Swagger UI 文档](https://swagger.io/tools/swagger-ui/)
- [ReDoc 文档](https://redocly.com/redoc/)
