
# Visie4web

## Setup:

1. Assegure-se de ter [mise-en-place](https://mise.jdx.dev/) instalado.

2. Entre na pasta do projeto e execute:

```
mise trust
python -m ensurepip
python -m pip install -r requirements.txt
```

3. Defina a senha do dashboard com:

```
py4web set_password
```

4. Crie o primeiro usuário com

```
py4web shell apps
from apps._default.scripts.createuser import createuser
createuser()
````

5. Execute o sistema

```
py4web run apps
```
