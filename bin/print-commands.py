from bottom import Client


def help_known_commands(client: Client) -> str:
    out = []
    all_templates = client._serializer.templates
    for command in sorted(all_templates.keys()):
        out.append(command)
        for tpl in all_templates[command]:
            out.append(f"  {tpl.original}")
        out.append("")
    return "\n".join(out)


my_client = Client("localhost", 6697)

print(help_known_commands(my_client))
