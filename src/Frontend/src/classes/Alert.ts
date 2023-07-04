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