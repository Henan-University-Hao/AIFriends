import { fetchEventSource } from '@microsoft/fetch-event-source';
import { useUserStore } from "@/stores/user.js";
import api, { getErrorMessage } from "./api.js";

const BASE_URL = 'http://127.0.0.1:8000'

export default async function streamApi(url, options = {}) {
    const userStore = useUserStore();

    const startFetch = async () => {
        return await fetchEventSource(BASE_URL + url, {
            method: options.method || 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${userStore.accessToken}`,
                ...options.headers,
            },
            body: JSON.stringify(options.body || {}),
            openWhenHidden: true,

            async onopen(response) {
                if (response.status === 401) {
                    try {
                        await api.post('/api/user/account/refresh_token/', {});
                        throw new Error("TOKEN_REFRESHED");
                    } catch (err) {
                        throw err;
                    }
                }

                if (response.status === 429) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.detail || '操作过快了，请稍后再试');
                }

                if (!response.ok || !response.headers.get('content-type')?.includes('text/event-stream')) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.detail || `请求失败: ${response.status}`);
                }
            },

            onmessage(msg) {
                if (msg.data === '[DONE]') {
                    if (options.onmessage) options.onmessage('', true);
                    return
                }
                try {
                    const json = JSON.parse(msg.data);
                    if (options.onmessage) options.onmessage(json, false);
                } catch (e) {
                    console.error("流解析失败:", e);
                }
            },

            onerror(err) {
                if (err.message === "TOKEN_REFRESHED") {
                    return startFetch();
                }

                if (options.onerror) {
                    options.onerror(new Error(getErrorMessage(err, '操作过快了，请稍后再试')));
                }
                throw err;
            },

            onclose: options.onclose,
        });
    };

    return await startFetch();
}
