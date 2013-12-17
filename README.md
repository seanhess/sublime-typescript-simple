A simplified sublime typescript plugin. 

![Screenshot](http://i.imgur.com/PHG6v39.png)

Motivation
----------

[Other sublime typescript plugin][t3s]s use a [subprocess][tss] that checks for errors. This subprocess is slow, error-prone, and doesn't necessarily reflect the errors reported by the real compiler. These will be fixed at some point, but I need a reliable typescript plugin now. 

This approach runs the normal TSC compiler, or whatever build you already have configured for your project. It displays the errors from your build in the window and in a panel at the bottom. 

Features

- Syntax Highlighting
- Error Highlighting
- Build on save
- Error Window

Limitations: we cannot support autocompletion, rafactoring, or other fancy IDE features with this simple approach. 

Installation
------------

Install [NodeJS](http://nodejs.org)

Go to your packages folder in Terminal. 

    cd Library/Application Support/Sublime Text 3/Packages

Clone this repository into that folder

    git clone http://github.com/seanhess/sublime-typescript-simple

Install the dependencies

    cd sublime-typescript-simple
    npm install

Configuration
-------------

By default, this plugin will compile files you open one at a time, displaying errors in each one. To better display errors for a whole project, you need to tell this plugin about your project. 

First, you need a sublime project. [Make one](http://www.sublimetext.com/forum/viewtopic.php?f=3&t=8694), open the project, then open the project file (Project -> Edit Project) to edit the settings.

This will sepecify a typescript file that should be checked along with any open file. Set this to your root file. 

    "typescript_main": "public/app.ts",

Alternatively, you can override the whole build command with any command that outputs the same thing as tsc

    "typescript_build": "grunt typescript:app",


Todo
-----

- warning: change to url of readme
- automatically install on clone?

[t3s]: https://github.com/Railk/T3S
[tss]: https://github.com/clausreinke/typescript-tools
[simple]: github.com/seanhess/sublime-typescript-simple