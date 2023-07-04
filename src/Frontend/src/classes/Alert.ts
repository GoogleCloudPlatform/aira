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
import { i18n } from "next-i18next";
import { toast } from "react-toastify";
import { ALERT_ERROR, ALERT_SUCCESS } from "@/constants/alert";

export default class Alert {
    constructor() {};

    alert(type = ALERT_ERROR, message : string) : void {
        if (type === ALERT_ERROR) toast.error(i18n?.t(message, { ns: "toast" }));
        if (type === ALERT_SUCCESS) toast.success(i18n?.t(message, { ns: "toast" }));
    }
}