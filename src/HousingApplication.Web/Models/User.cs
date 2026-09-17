namespace FileOrganizer.Web.Models;

public class User
{
    public int Id { get; set; }
    public string Username { get; set; } = string.Empty;
    public string DisplayName { get; set; } = string.Empty;
    public string PasswordHash { get; set; } = string.Empty;
    public string Salt { get; set; } = string.Empty;
    public string Role { get; set; } = "Contributor"; // "Admin" or "Contributor"
    public string CreatedAt { get; set; } = string.Empty;
    public int IsActive { get; set; } = 1;
}

public class UserDto
{
    public int Id { get; set; }
    public string Username { get; set; } = string.Empty;
    public string DisplayName { get; set; } = string.Empty;
    public string Role { get; set; } = string.Empty;
    public bool CanDelete => string.Equals(Role, "Admin", StringComparison.OrdinalIgnoreCase);
}

public class LoginRequestDto
{
    public string Username { get; set; } = string.Empty;
    public string? Password { get; set; }
}

public class LoginResponseDto
{
    public bool Success { get; set; }
    public string? Message { get; set; }
    public UserDto? User { get; set; }
}

public class AuthStatusResponseDto
{
    public bool Authenticated { get; set; }
    public UserDto? User { get; set; }
}
