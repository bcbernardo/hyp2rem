---
title: Hyp2Rem
alternative: "Readme"
description: "Hypothes.is to RemNote integration"
creator: "/AUTHORS.md"
created: "2020-12-12"
license: "/LICENSE"

---

# Hyp2Rem

Hypothes.is to RemNote integration

This utility retrieves your Hypothes.is annotations and uploads them as Rems
in your RemNote account. In other words, you can easily annotate any web page
or PDF using Hypothes.is free and open source collaborative annotation tool
while browsing it. Hyp2Rem can then be configured to fetch all your notes and
transform your them into Rems in your knowledge base, so that you can enjoy
RemNote's backlinking and spaced repetition features.

## Table of Contents

- [Install](#install)
  - [Get your credentials](#get-your-credentials)
- [Usage](#usage)
  - [CLI](#cli)
- [Contributing](#contributing)
- [License](#license)

## Install

You can install the package directly into a virtual environment using  `pip`
and a tool like `venv`.

In Unix/MacOS systems:

```sh
python3 -m venv example-env
source example-env/bin/activate
python -m pip install git+https://github.com/inova-mprj/bussola-etl-siafe
```

In Windows:

```sh
python3 -m venv example-env
example-env\Scripts\activate.bat
python -m pip install git+https://github.com/inova-mprj/bussola-etl-siafe
```

Alternatively, you can use `pipx` (see [pipx documentation][pipx install] on
how to install `pipx`) to handle the environment isolation automagically:

```sh
pipx install git+https://github.com/inova-mprj/bussola-etl-siafe
```

If you plan to use the package as a dependency in your workflow, you can
install it using a dependency manager like `pipenv` or `poetry`:

```sh
# Pipenv
pipenv add git+https://github.com/inova-mprj/bussola-etl-siafe
```

```sh
# Poetry
poetry add git+https://github.com/inova-mprj/bussola-etl-siafe
```

[pipx install]: https://pipxproject.github.io/pipx/installation/

### Get your credentials

Before you can even start to play with Hyp2Rem, you must get some special
credentials both in Hypothes.is and RemNote web apps. Follow [this
tutorial][/docs/get-access.md] to generate your keys.

## Usage

### CLI

```sh
# Fetch all annotations updated after Jan, 1st 2020 in an annotation group
# named 'RemNote' (case-sensitive)
hyp2rem --hyp-group="RemNote" --sort="updated" --after="2020-01-01"
```

## Contributing

Contributions for this project are welcome.

Check for [open issues] that might need someone's attention, or [open a new
issue] if you have found a bug or want to propose an enhancement.

To work in a new feature or solve a bug, [fork] this repository and open a
[new pull request] once you have a working solution for review.

Oh, and please make sure you follow the [Code of Conduct] in all of your
interactions.

[open issues]: https://github.com/bcbernardo/hyp2rem/issues
[open a new issue]: https://github.com/bcbernardo/hyp2rem/issues/new/choose
[fork]: https://github.com/bcbernardo/hyp2rem/fork
[new Pull Request]: https://github.com/bcbernardo/hyp2rem/compare
[Code of Conduct]: https://github.com/bcbernardo/hyp2rem/CODE_OF_CONDUCT.md

## License

Copyright 2020 [The Hyp2Rem Authors](/AUTHORS.md)

Use of this source code is governed by an MIT license that can be found in the
[LICENSE](/LICENSE) file or at <https://opensource.org/licenses/MIT>.