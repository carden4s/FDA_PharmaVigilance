"""Caching utilities for Streamlit"""

import streamlit as st
from datetime import timedelta


def cache_data(ttl_hours: int = 1):
    """Cache data for specified hours"""
    return st.cache_data(ttl=timedelta(hours=ttl_hours))
