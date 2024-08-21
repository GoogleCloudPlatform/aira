import { toast } from "react-toastify";
import { ALERT_ERROR, ALERT_SUCCESS } from "@/constants/alerts";
import { getMessages } from "@/libs/i18n/i18n-config";

export default class Alert {
    constructor() {
        this.alert = this.alert.bind(this);
    };

    async alert(type = ALERT_ERROR, key : string) : Promise<void> {
        const [_, locale] = window.location.pathname.split("/");
        
        const messages = await getMessages(locale);
        const message = messages[key];

        if (type === ALERT_ERROR) toast.error(message);
        if (type === ALERT_SUCCESS) toast.success(message);
    }
}