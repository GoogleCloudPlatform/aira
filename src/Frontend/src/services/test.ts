import Alert from "@/classes/Alert";
import { ALERT_ERROR } from "@/constants/alert";
import { api } from "@/pages/api/api";

const AlertInstance = new Alert();

export async function getTest() : Promise<any> {
    return new Promise<any>(async (resolve, reject) => {
        try {
            const data = await api.get("/");
            resolve(data);
        } catch (e) {
            console.log(e);
            AlertInstance.alert(ALERT_ERROR, 'error_api');
            reject(null);
        }
    });
}