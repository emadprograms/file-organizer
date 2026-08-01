[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using System.Text;

[ComImport, Guid("00021401-0000-0000-C000-000000000046"), ClassInterface(ClassInterfaceType.None)]
public class ShellLink {}

[ComImport, Guid("000214F9-0000-0000-C000-000000000046"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IShellLinkW {
    void GetPath([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszFile, int cchMaxPath, IntPtr pfd, uint fFlags);
    void GetIDList(out IntPtr ppidl);
    void SetIDList(IntPtr pidl);
    void GetDescription([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszName, int cchMaxName);
    void SetDescription([MarshalAs(UnmanagedType.LPWStr)] string pszName);
    void GetWorkingDirectory([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszDir, int cchMaxPath);
    void SetWorkingDirectory([MarshalAs(UnmanagedType.LPWStr)] string pszDir);
    void GetArguments([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszArgs, int cchMaxPath);
    void SetArguments([MarshalAs(UnmanagedType.LPWStr)] string pszArgs);
    void GetHotkey(out short pwHotkey);
    void SetHotkey(short wHotkey);
    void GetShowCmd(out int piShowCmd);
    void SetShowCmd(int iShowCmd);
    void GetIconLocation([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszIconPath, int cchIconPath, out int piIcon);
    void SetIconLocation([MarshalAs(UnmanagedType.LPWStr)] string pszIconPath, int iIcon);
    void SetRelativePath([MarshalAs(UnmanagedType.LPWStr)] string pszPathRel, uint dwReserved);
    void Resolve(IntPtr hwnd, uint fFlags);
    void SetPath([MarshalAs(UnmanagedType.LPWStr)] string pszFile);
}

public class ShortcutInterop {
    public static void Create(string target, string link) {
        IShellLinkW sl = (IShellLinkW)new ShellLink();
        sl.SetPath(target);
        IPersistFile pf = (IPersistFile)sl;
        pf.Save(link, false);
    }
    public static string Read(string link) {
        IShellLinkW sl = (IShellLinkW)new ShellLink();
        IPersistFile pf = (IPersistFile)sl;
        pf.Load(link, 0);
        StringBuilder sb = new StringBuilder(32767);
        sl.GetPath(sb, sb.Capacity, IntPtr.Zero, 0);
        return sb.ToString();
    }
}
"@

$action = $args[0]

if ($action -eq "create") {
    $target = $args[1]
    $link = $args[2]
    [ShortcutInterop]::Create($target, $link)
} elseif ($action -eq "batch-create") {
    $inputJson = [Console]::In.ReadToEnd()
    if (![string]::IsNullOrWhiteSpace($inputJson)) {
        $items = $inputJson | ConvertFrom-Json
        foreach ($item in $items) {
            try {
                [ShortcutInterop]::Create($item.target, $item.link)
            } catch {
                Write-Error "Failed to create shortcut $($item.link): $_"
            }
        }
    }
} elseif ($action -eq "batch-read") {
    $inputJson = [Console]::In.ReadToEnd()
    $results = @{}
    if (![string]::IsNullOrWhiteSpace($inputJson)) {
        $links = $inputJson | ConvertFrom-Json
        foreach ($link in $links) {
            try {
                $target = [ShortcutInterop]::Read($link)
                $results[$link] = $target
            } catch {
                $results[$link] = $null
            }
        }
    }
    $resultsJson = $results | ConvertTo-Json -Depth 5 -Compress
    Write-Output $resultsJson
}
