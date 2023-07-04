"""
Module to startup the server
"""
import api

app = api.create_app(api.create_container())
