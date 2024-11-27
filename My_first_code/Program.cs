using System;
public class Program
{
    public static void Main()
    {
        string a = Console.ReadLine();
        string b = Console.ReadLine();
        bool isAdmin = Program.Login(a, b);
        if (isAdmin)
        {
            Console.WriteLine("Ugurlu");
            ShowUser(username);
        }
        else
        {
            Console.WriteLine("ugursuz");
        }
        Logout();
    }
    static bool Login(string name, string password)
    {
        if (name == "qurban" && password == "1234")
        {
            return true;
        }
        return false;
    }
    static void Logout()
    {
        Console.WriteLine("logged out");
    }
    static void ShowUser(string username)
    {
        Console.WriteLine("you are" + username);
    }
}
