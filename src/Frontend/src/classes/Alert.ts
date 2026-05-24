import { toast } from "react-toastify";
import { ALERT_ERROR, ALERT_SUCCESS } from "@/constants/alerts";
import { getMessages } from "@/libs/i18n/i18n-config";

export default class Alert {
    constructor() {
        this.alert = this.alert.bind(this);
    };

    async alert(type = ALERT_ERROR, key : string) : Promise<void> {
        const [_, locale] = window.location.pathname.split("/");
        
        const messages = await getMessages(locale as any);
        
        const getNestedValue = (obj: any, path: string) => {
            return path.split('.').reduce((acc, part) => acc && acc[part], obj);
        }
        
        const message = getNestedValue(messages, key) || getNestedValue(messages, 'toast.errors.auth.error_api') || "Request error";

        if (type === ALERT_ERROR) toast.error(message);
        if (type === ALERT_SUCCESS) toast.success(message);
    }
}