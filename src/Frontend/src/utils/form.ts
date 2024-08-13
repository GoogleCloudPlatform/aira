import { IExamsResponse } from "@/interfaces/exam";
import { TDependsOfRules, TFormFields, TInput, TOption, TSelect } from "@/interfaces/form";
import { IGroupsResponse } from "@/interfaces/group";
import { IOrganization, IOrganizationResponse, IOrganizationsResponse, IOrganizationsUtilsResponse } from "@/interfaces/organization";
import { IRoleResponse, IRolesResponse } from "@/interfaces/roles";
import { getExams } from "@/services/exam";
import { getAllGroups } from "@/services/group";
import { getAllOrganizations } from "@/services/organization";
import { getAllRoles } from "@/services/role";
import { TElement } from "@udecode/plate-common";
import { isEmpty } from "lodash";
import { usePathname } from "next/navigation";
import Router, { useRouter } from "next/router";
import { FieldValues, UseFormWatch } from "react-hook-form";


/**
 * This function is tighly acomplated with the backend api response.
 * It parses the items array from api list's to the TOption type notation.
 * Meant to be used on HTML selects.
 * [{ ... }] => [{ label, value }]
 * @param {data} data - api response
 * @returns {TOption[]} - return TOption array
*/
export const mapToOptionType = (data: IOrganizationsResponse | IGroupsResponse | IExamsResponse | IRolesResponse) : Array<TOption> => {
    if (!data) return [];

    return data.items.map((item: any) => { 
        /**
         * treats the case where the response is from IRolesResponse
         */
        if (item.display_name) {
            const [_, locale] = window.location.pathname.split("/");
            if (item.display_name[locale]) {
                return { label: item.display_name[locale], value: item.id, ...item }
            }        
        }

        return { label: item.name, value: item.id, ...item }
    });
}


/**
* Fetches options for a select field based on the field name.
* For 'organizations' field, retrieves options from all organizations.
* For 'groups' field, retrieves options from all groups.
* @param {string} fieldName - The name of the field for which options are requested.
* @returns {Promise<TOption[]>} - A promise resolving to an array of TOption objects.
*/
export const getOptions = async (fieldName: 'organizations' | 'groups' | 'roles' | 'exams') : Promise<TOption[]> => {
    if (fieldName === "organizations") {
        const response = await getAllOrganizations();
        const options = mapToOptionType(response);
        return options;
    }

    if (fieldName === "groups") {
        const response = await getAllGroups();
        const options = mapToOptionType(response);
        return options;
    }

    if (fieldName === "exams") {
        const response = await getExams();
        const options = mapToOptionType(response);
        return options;
    }

    if (fieldName === "roles") {
        const response = await getAllRoles();
        const options = mapToOptionType(response);
        return options;
    }
    return [];
}

/**
 * Removes HTML tags from the given text.
 * 
 * @param {string} text - The text containing HTML tags.
 * @returns {string} - The text with HTML tags removed.
 */
// export const removeHTMLTags = (text: string) => {
//     text = text.replace(/<p\s*\/?>/gi, '##PARAGRAPH##');
//     text = text.replace(/<p\s[^>]*>/gi, '##PARAGRAPH##');
//     text = text.replace(/<[^>]*>|&nbsp;/g, match => {
//         if (match === '&nbsp;') {
//             return ' ';
//         } else {
//             return '';
//         }
//     });
//     text = text.replace(/##PARAGRAPH##/g, ' ');

//     return text.trim();
// }

export const convertTextEditorData = (text: string) => {
    const data = JSON.parse(text).map((children: TElement) => children.children[0].text).join(' ').replace(/\s+/g, ' ')

    return data
}

// /**
//  * Removes <script> tags from the given text.
//  * 
//  * @param {string} text - The text containing <script> tags.
//  * @returns {string} - The text with <script> tags removed.
//  */
// export function removeScripTags(text: string) {
//     text = text.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
//     text = text.replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, '');

//     return text;
// }