#!/usr/bin/env python3
from monitor import SingleCheckMonitor

checker = SingleCheckMonitor()
print(checker.check_site("https://www.google.com"))
print(checker.check_site("https://noexiste123456.com"))
