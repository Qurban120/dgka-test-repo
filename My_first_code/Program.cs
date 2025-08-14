using System.Text;
using System.Text.Json;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddRouting();
builder.Services.AddCors(options =>
{
	options.AddDefaultPolicy(policy =>
	{
		policy.AllowAnyOrigin().AllowAnyHeader().AllowAnyMethod();
	});
});

var app = builder.Build();

app.UseCors();

// Serve x.html as the default file
var defaultFiles = new DefaultFilesOptions();
defaultFiles.DefaultFileNames.Clear();
defaultFiles.DefaultFileNames.Add("x.html");
app.UseDefaultFiles(defaultFiles);

app.UseStaticFiles();

app.MapGet("/api/data", (IWebHostEnvironment env) =>
{
	var path = Path.Combine(env.WebRootPath ?? string.Empty, "kri-data.json");
	if (!System.IO.File.Exists(path))
	{
		return Results.NotFound(new { error = "kri-data.json not found" });
	}
	var json = System.IO.File.ReadAllText(path, Encoding.UTF8);
	return Results.Content(json, "application/json", Encoding.UTF8);
});

app.MapPost("/api/data", async (IWebHostEnvironment env, HttpRequest request) =>
{
	using var reader = new StreamReader(request.Body, Encoding.UTF8);
	var body = await reader.ReadToEndAsync();
	try
	{
		// Validate JSON
		using var _ = JsonDocument.Parse(body);
	}
	catch (JsonException ex)
	{
		return Results.BadRequest(new { error = "Invalid JSON payload", detail = ex.Message });
	}

	var path = Path.Combine(env.WebRootPath ?? string.Empty, "kri-data.json");
	Directory.CreateDirectory(Path.GetDirectoryName(path)!);
	await System.IO.File.WriteAllTextAsync(path, body, new UTF8Encoding(false));
	return Results.Ok(new { success = true });
});

// Simple health endpoint
app.MapGet("/api/health", () => Results.Ok(new { status = "ok" }));

app.Run();
