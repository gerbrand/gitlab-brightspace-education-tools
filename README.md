# Starting a new semester with Gitlab
At the [university](https://www.hva.nl) I'm teaching, we have a Brightspace environment education needs and a Gitlab environment where students can publish their code.

This repository (will) contain a scripts and tools to sync both enviorments.

As a start, I've created a simple script to help me start a new semester with Gitlab. Uses list of students from CSV file, that's exported from our Brightspace environment. Than use that list to prepare new repositories.


This project is in early development stage. Documentation and blog post will follow soon!

# Installation

Required development tools:
* Python 3
* [uv])(https://docs.astral.sh/uv/)


* Rename [gl.cfg.example](gl.cfg.example) to gl.cfg and update the file. Add/replace your own gitlab address and add a personal token
* Rename [semester_in_gitlab.ini](semester_in_gitlab.ini.example). Add your subject your giving 