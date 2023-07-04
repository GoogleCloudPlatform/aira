// Copyright 2022 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
export const ROLE_ADMIN = "admin";
export const ROLE_EDUCATOR = "teacher";
export const ROLE_LEARNER = "student";

export const SCOPE_ADMIN = "admin";
export const SCOPE_EDUCATOR = "semi-admin";
export const SCOPE_LEARNER = "user";
export const SCOPE_USER = "user";
export const SCOPE_DASHBOARD_VIEWER = "dashboard.viewer";

export const ROLES : Array<string> = [ROLE_ADMIN, ROLE_EDUCATOR, ROLE_LEARNER];
export const SCOPES : Array<string> = [ROLE_ADMIN, ROLE_EDUCATOR, ROLE_LEARNER];