using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Web.Script.Serialization;

public class CodexNativeFocus {
    static string Root = AppDomain.CurrentDomain.BaseDirectory;
    static JavaScriptSerializer Json = new JavaScriptSerializer();
    public delegate bool Callback(IntPtr hwnd, IntPtr arg);
    [DllImport("user32.dll")] static extern bool EnumWindows(Callback cb, IntPtr arg);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr hwnd);
    [DllImport("user32.dll")] static extern bool IsWindow(IntPtr hwnd);
    [DllImport("user32.dll")] static extern bool IsIconic(IntPtr hwnd);
    [DllImport("user32.dll")] static extern bool IsZoomed(IntPtr hwnd);
    [DllImport("user32.dll")] static extern bool ShowWindowAsync(IntPtr hwnd, int command);
    [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr hwnd);
    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetWindowText(IntPtr hwnd, StringBuilder text, int count);
    [StructLayout(LayoutKind.Sequential)] struct Keyboard { public ushort vk,scan; public uint flags,time; public UIntPtr extra; }
    [StructLayout(LayoutKind.Sequential)] struct Mouse { public int x,y; public uint data,flags,time; public UIntPtr extra; }
    [StructLayout(LayoutKind.Explicit)] struct InputUnion { [FieldOffset(0)] public Keyboard keyboard; [FieldOffset(0)] public Mouse mouse; }
    [StructLayout(LayoutKind.Sequential)] struct Input { public uint type; public InputUnion value; }
    [DllImport("user32.dll",SetLastError=true)] static extern uint SendInput(uint count,Input[] inputs,int size);
    [DllImport("user32.dll")] static extern short GetAsyncKeyState(int key);
    static string Title(IntPtr hwnd) { var s = new StringBuilder(2048); GetWindowText(hwnd,s,s.Capacity); return s.ToString(); }
    static void Log(string status, object data) {
        File.AppendAllText(Path.Combine(Root,"native-focus.jsonl"), Json.Serialize(new { time=DateTime.Now.ToString("o"),status=status,data=data })+Environment.NewLine);
    }
    static Dictionary<string,object> Read(string file) { return Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(file)); }
    static string TicketPath(string token) { return Path.Combine(Root,"native-tickets",token+".json"); }
    static IntPtr Find(string workspace) {
        var list = new List<IntPtr>();
        string pattern=Regex.Escape(" - "+workspace)+@"(?: \[WSL: [^\]]+\])? - Visual Studio Code(?: - Insiders)?$";
        EnumWindows(delegate(IntPtr hwnd, IntPtr arg) {
            if (!IsWindowVisible(hwnd) || !Regex.IsMatch(Title(hwnd),pattern)) return true;
            uint pid; GetWindowThreadProcessId(hwnd,out pid);
            try { string name=Process.GetProcessById((int)pid).ProcessName;
                if (name=="Code" || name=="Code - Insiders") list.Add(hwnd);
            } catch { }
            return true;
        },IntPtr.Zero);
        if (list.Count != 1) throw new Exception("Cannot select native VS Code window: "+list.Count+" matches for "+workspace);
        return list[0];
    }
    static void Bind(string token,string workspace) {
        IntPtr hwnd=Find(workspace); uint pid; GetWindowThreadProcessId(hwnd,out pid);
        Directory.CreateDirectory(Path.GetDirectoryName(TicketPath(token)));
        File.WriteAllText(TicketPath(token),Json.Serialize(new { handle=hwnd.ToInt64(),pid=pid,
            processStart=Process.GetProcessById((int)pid).StartTime.ToUniversalTime().Ticks,workspace=workspace }));
    }
    static IntPtr Bound(string token) {
        var row=Read(TicketPath(token)); IntPtr hwnd=new IntPtr(Convert.ToInt64(row["handle"]));
        uint pid; GetWindowThreadProcessId(hwnd,out pid);
        if (!IsWindow(hwnd) || pid!=Convert.ToUInt32(row["pid"]) ||
            Process.GetProcessById((int)pid).StartTime.ToUniversalTime().Ticks!=Convert.ToInt64(row["processStart"]))
            throw new Exception("The original VS Code window has closed");
        return hwnd;
    }
    static bool Focus(IntPtr hwnd) {
        if (IsIconic(hwnd)) { ShowWindowAsync(hwnd,9); Thread.Sleep(80); }
        bool requested=SetForegroundWindow(hwnd);
        for (int i=0;i<10;i++) { if(GetForegroundWindow()==hwnd) return true; Thread.Sleep(30); }
        // A notification click explicitly requests activation. Release Windows' foreground lock
        // with a balanced ALT pair only when no modifier is physically held.
        if ((GetAsyncKeyState(0x12)&0x8000)==0 && (GetAsyncKeyState(0x11)&0x8000)==0 &&
            (GetAsyncKeyState(0x10)&0x8000)==0 && (GetAsyncKeyState(0x5b)&0x8000)==0) {
            var keys=new Input[2];
            keys[0].type=1; keys[0].value.keyboard.vk=0x12;
            keys[1].type=1; keys[1].value.keyboard.vk=0x12; keys[1].value.keyboard.flags=2;
            uint sent=SendInput(2,keys,Marshal.SizeOf(typeof(Input)));
            Log("activation-retry",new{target=hwnd.ToInt64(),keyboardEvents=sent});
            SetForegroundWindow(hwnd);
        }
        for(int i=0;i<10;i++) { if(GetForegroundWindow()==hwnd) return true; Thread.Sleep(30); }
        Log("foreground-refused",new{target=hwnd.ToInt64(),foreground=GetForegroundWindow().ToInt64(),requested=requested});
        return false;
    }
    [STAThread]
    public static int Main(string[] args) {
        try {
            if(args.Length==3 && args[0]=="--bind") { Bind(Guid.Parse(args[1]).ToString(),args[2]); return 0; }
            if(args.Length!=1) throw new Exception("Expected one notification URI");
            var match=Regex.Match(args[0],@"^codex-session://focus/([0-9a-f-]{36})/?$");
            if(!match.Success) throw new Exception("Invalid notification URI");
            string token=Guid.Parse(match.Groups[1].Value).ToString();
            IntPtr hwnd=IntPtr.Zero; bool maximized=false;
            if(File.Exists(TicketPath(token))) {
                hwnd=Bound(token); maximized=IsZoomed(hwnd);
                Log("click-target",new{token=token,handle=hwnd.ToInt64(),title=Title(hwnd),maximized=maximized});
                Focus(hwnd); // The user-launched GUI process activates the window immediately.
            }
            var config=Read(Path.Combine(Root,"click-config.json"));
            string arguments=config["bridgeArguments"].ToString()+" "+token;
            Log("bridge-launch",new{arguments=arguments,user=Environment.UserName,is64=Environment.Is64BitProcess,root=Root});
            var start=new ProcessStartInfo(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Windows),"System32","wsl.exe"),arguments);
            start.UseShellExecute=false; start.CreateNoWindow=true; start.RedirectStandardOutput=true; start.RedirectStandardError=true; start.RedirectStandardInput=true;
            start.StandardOutputEncoding=Encoding.UTF8; start.StandardErrorEncoding=Encoding.UTF8;
            string output,error; int exit;
            using(var child=Process.Start(start)) {
                child.StandardInput.Close();
                var stdout=child.StandardOutput.ReadToEndAsync(); var stderr=child.StandardError.ReadToEndAsync();
                if(!child.WaitForExit(20000)) { child.Kill(); throw new Exception("WSL terminal focus timed out"); }
                output=stdout.Result; error=stderr.Result; exit=child.ExitCode;
            }
            if(exit!=0) throw new Exception("WSL bridge exit="+exit+" stdout="+output+" stderr="+error);
            var response=Json.Deserialize<Dictionary<string,object>>(output);
            if(hwnd==IntPtr.Zero) {
                var workspaces=(System.Collections.IEnumerable)response["workspace"];
                string workspace=null; foreach(object w in workspaces) { workspace=Path.GetFileName(w.ToString().TrimEnd('/')); break; }
                if(workspace==null) throw new Exception("Missing original workspace");
                hwnd=Find(workspace); maximized=IsZoomed(hwnd);
            }
            bool focused=Focus(hwnd);
            Log(focused?"activated":"activation-failed",new{token=token,handle=hwnd.ToInt64(),foreground=GetForegroundWindow().ToInt64(),maximizedBefore=maximized,maximizedAfter=IsZoomed(hwnd),terminal=response});
            return focused?0:1;
        } catch(Exception e) { try{Log("error",new{detail=e.ToString()});}catch{} return 1; }
    }
}
