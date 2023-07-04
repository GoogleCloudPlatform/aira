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
import Alert from "@/classes/Alert";
import { ALERT_ERROR } from "@/constants/alert";
import { ENDPOINT_EXAMS } from "@/constants/endpoint";
import { IQuestion, IQuestionResponse } from "@/interfaces/question";
import { api } from "@/pages/api/api";

const AlertInstance = new Alert();

export async function getQuestionById(id : string) : Promise<IQuestionResponse> {
    return new Promise<IQuestionResponse>(async (resolve, reject) => {
        try {
            const data : IQuestionResponse = {
             
            }
            resolve(data);
        } catch (e) {
            console.error(e);
            AlertInstance.alert(ALERT_ERROR, 'error_api');
            reject(null);
        }
    });
}