A simplified sublime typescript plugin. 

Motivation
----------

[Other sublime typescript plugin][t3s]s use a [subprocess][tss] that checks for errors. This subprocess is slow, error-prone, and doesn't necessarily reflect the errors reported by the real compiler. These will be fixed at some point, but I need a reliable typescript plugin now. 

This approach will not support autocomplete, but it will make you more productive :) It supports the following features:

- Syntax Highlighting
- Error Highlighting
- Build on save
- Error Window

Installation
------------

Install this Package (Terminal)

```
cd your/sublime/packages/folder
git clone http://github.com/seanhess/sublime-typescript-simple
```

Install [NodeJS](http://nodejs.org)

Configuration
-------------

By default, this plugin will compile files you open one at a time, displaying errors in each one. To better display errors for a whole project, you need to tell this plugin about your project. 

First, you need a sublime project. Make one, then open the sublime project file and edit these settings:

```
{
    "settings":
    {
        // this file will be built every time in addition to the open file
        "typescript_main": "public/app.ts",

        // use this build command instead of tsc. It must output typescript errors!
        "typescript_build": "grunt typescript:app",
    }       
}
```

[t3s]: https://github.com/Railk/T3S
[tss]: https://github.com/clausreinke/typescript-tools
[simple]: github.com/seanhess/sublime-typescript-simple