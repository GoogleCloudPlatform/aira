"""
Specific strategies for hypothesis.
"""

import functools

from hypothesis import strategies as st

safe_characters = functools.partial(
    st.characters,
    blacklist_categories=[
        "Cs",  # Surrrogate
    ],
    blacklist_characters=["\x00"],
)

safe_text = functools.partial(
    st.text,
    alphabet=safe_characters(),
)

create_role = st.fixed_dictionaries(
    {"name": safe_text(), "scopes": st.lists(safe_text(), min_size=1)}
)
