# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
