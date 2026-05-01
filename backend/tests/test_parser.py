"""
Tests for the code parser engine.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.parser import parse_file, detect_language


class TestDetectLanguage:
    def test_python(self):
        assert detect_language("main.py") == "python"
        assert detect_language("src/utils.py") == "python"

    def test_javascript(self):
        assert detect_language("index.js") == "javascript"
        assert detect_language("src/App.jsx") == "javascript"

    def test_typescript(self):
        assert detect_language("index.ts") == "typescript"
        assert detect_language("App.tsx") == "typescript"

    def test_java(self):
        assert detect_language("Main.java") == "java"

    def test_go(self):
        assert detect_language("main.go") == "go"

    def test_unknown(self):
        assert detect_language("readme.md") == "unknown"
        assert detect_language("Dockerfile") == "unknown"


class TestParsePython:
    def test_import_extraction(self):
        content = """
import os
import sys
from pathlib import Path
from . import utils
from ..helpers import format_output

def main():
    pass

class MyClass:
    pass
"""
        result = parse_file("test.py", content)
        assert result["language"] == "python"
        assert "os" in result["imports"]
        assert "sys" in result["imports"]
        assert "pathlib" in result["imports"]
        assert "main" in result["declarations"]
        assert "MyClass" in result["declarations"]

    def test_empty_file(self):
        result = parse_file("empty.py", "")
        assert result["language"] == "python"
        assert result["imports"] == []
        assert result["declarations"] == []

    def test_exports(self):
        content = """
def public_function():
    pass

def _private_function():
    pass

class PublicClass:
    pass
"""
        result = parse_file("module.py", content)
        assert "public_function" in result["exports"]
        assert "PublicClass" in result["exports"]


class TestParseJavaScript:
    def test_import_extraction(self):
        content = """
import React from 'react';
import { useState, useEffect } from 'react';
import './styles.css';
const axios = require('axios');

export function App() {
    return null;
}

export default class Header {
}
"""
        result = parse_file("App.js", content)
        assert result["language"] == "javascript"
        assert "react" in result["imports"]
        assert "axios" in result["imports"]
        assert "App" in result["declarations"] or "App" in result["exports"]

    def test_typescript_same_parser(self):
        content = """
import { Router } from 'express';
export const router = Router();
"""
        result = parse_file("routes.ts", content)
        assert result["language"] == "typescript"
        assert "express" in result["imports"]


class TestParseJava:
    def test_java_imports(self):
        content = """
import java.util.List;
import java.io.File;

public class Main {
    public static void main(String[] args) {
    }
}
"""
        result = parse_file("Main.java", content)
        assert result["language"] == "java"
        assert "java.util.List" in result["imports"]
        assert "Main" in result["declarations"]


class TestParseMultiLanguage:
    def test_c_includes(self):
        content = """
#include <stdio.h>
#include "utils.h"

int main() {
    return 0;
}
"""
        result = parse_file("main.c", content)
        assert result["language"] == "c"
        assert "stdio.h" in result["imports"]
        assert "utils.h" in result["imports"]

    def test_rust_use(self):
        content = """
use std::io;
use crate::utils;

fn main() {
    println!("Hello");
}
"""
        result = parse_file("main.rs", content)
        assert result["language"] == "rust"
        assert "std::io" in result["imports"]
        assert "main" in result["declarations"]
