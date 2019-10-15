using System;
using System.Collections;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Text;
using UnityEditor;
using UnityEngine;
using UnityEngine.Experimental.UIElements;
using UnityEngine.Networking;

public class NetworkClientBehaviourScript : MonoBehaviour
{
    //private NetworkClientThread nct = null;

    [Serializable]
    class Msg
    {
        [SerializeField] public string MsgType;
        [SerializeField] public string DeviceName;
    }

    [Serializable]
    class MsgLog : Msg
    {
        public MsgLog(string deviceName, string data)
        {
            MsgType = "log";
            this.data = data;
            this.DeviceName = deviceName;
        }

        [SerializeField] public string data;
    }

    [Serializable]
    class MsgDataFrame : Msg
    {
        public MsgDataFrame(string deviceName, string dataname, float frametime, float framevalue)
        {
            this.MsgType = "dataframe";
            this.DeviceName = deviceName;
            this.dataname = dataname;
            this.time = frametime;
            this.value = framevalue;
        }

        [SerializeField] public string dataname;
        [SerializeField] public float time;
        [SerializeField] public float value;
    }

    public string HostName = null;

    private string DeviceName = "";    
    private int Port = 9999;

    // Start is called before the first frame update
    void Awake()
    {
        DeviceName = SystemInfo.deviceName;
        if (string.IsNullOrEmpty(HostName))
            HostName = Dns.GetHostName();

        Application.logMessageReceived += LogCallback;
        //nct = new NetworkClientThread(SystemInfo.deviceName);
        //nct.Start();
    }

    public void LogCallback(string condition, string stackTrace, LogType type)
    {
        //nct.SendLog(condition);
        StartCoroutine(Post(GetServerURL(), LogMsgToJson(condition)));
    }

    private void OnDestroy()
    {        
        //nct.Dispose();
    }

    public string LogMsgToJson(string data)
    {
        return JsonUtility.ToJson(new MsgLog(DeviceName, data));
    }

    public string DataFrameMsgToJson(string dataname, float x, float y)
    {
        return JsonUtility.ToJson(new MsgDataFrame(DeviceName, dataname, x, y));
    }

    private IPAddress GetIPV4(IPHostEntry HostInformation)
    {
        IPAddress[] IP = HostInformation.AddressList;
        int index = 0;
        foreach (IPAddress Address in IP)
        {
            if (Address.AddressFamily.Equals(AddressFamily.InterNetwork))
            {
                break;
            }
            index++;
        }
        return HostInformation.AddressList[index];
    }

    private string GetServerURL()
    {
        IPHostEntry ipHost = Dns.GetHostEntry(HostName);
        IPAddress ipAddr = GetIPV4(ipHost);        
        return string.Format("http://{0}:{1}", ipAddr, Port);
    }

    IEnumerator Post(string url, string bodyJsonString)
    {
        var request = new UnityWebRequest(url, "POST");
        byte[] bodyRaw = Encoding.UTF8.GetBytes(bodyJsonString);
        request.uploadHandler = (UploadHandler)new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = (DownloadHandler)new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        yield return request.SendWebRequest();

        //Debug.Log("Status Code: " + request.responseCode);
    }

    int m_Frames = 0;
    float m_FPSTime = 0.0f;
    float m_FPS = 0.0f;

    void Update()
    {
        m_Frames++;
        m_FPSTime += Time.deltaTime;
        const float calcTime = 1.0f;
        if (m_FPSTime > calcTime)
        {
            m_FPS = m_Frames;
            m_FPS /= m_FPSTime;

            m_FPSTime = 0.0f;
            m_Frames = 0;
            StartCoroutine(Post(GetServerURL(), DataFrameMsgToJson("fps", Time.time, m_FPS)));
        }
    }

    [ContextMenu("test")]
    public void Test()
    {
        Debug.Log(string.Format("\n[{0,-10}]\n[{0,10}]", 128));
        Debug.Log(string.Format("[{0,-11}]", int.MaxValue));
    }
}
