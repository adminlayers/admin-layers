"""
Anvil Server Module: Demo Mode
Provides sample data for demonstration purposes
"""
import anvil.server

# Demo data
DEMO_USERS = [
    {"id": f"user-{i:04d}", "name": name, "email": f"{name.lower().replace(' ', '.')}@acmecorp.com",
     "department": dept, "title": title, "state": "active"}
    for i, (name, dept, title) in enumerate([
        ("Alice Johnson", "Support", "Senior Agent"),
        ("Bob Martinez", "Support", "Team Lead"),
        ("Carol Williams", "Sales", "Account Executive"),
        ("David Chen", "Support", "Agent"),
        ("Emma Davis", "Engineering", "Developer"),
        ("Frank Wilson", "Support", "Senior Agent"),
        ("Grace Lee", "Sales", "Sales Manager"),
        ("Henry Brown", "Support", "Agent"),
        ("Iris Taylor", "QA", "Quality Analyst"),
        ("James Anderson", "Support", "Agent"),
        ("Karen Thomas", "Support", "Supervisor"),
        ("Liam Jackson", "Sales", "SDR"),
        ("Maria Garcia", "Support", "Agent"),
        ("Nathan White", "Engineering", "DevOps Engineer"),
        ("Olivia Harris", "Support", "Senior Agent"),
        ("Patrick Martin", "Support", "Agent"),
        ("Quinn Robinson", "Sales", "Account Manager"),
        ("Rachel Clark", "Support", "Agent"),
        ("Samuel Lewis", "QA", "QA Lead"),
        ("Tina Walker", "Support", "Agent"),
    ])
]

DEMO_GROUPS = [
    {"id": "group-0001", "name": "Tier 1 Support", "type": "official", "visibility": "public", "memberCount": 12},
    {"id": "group-0002", "name": "Tier 2 Support", "type": "official", "visibility": "public", "memberCount": 5},
    {"id": "group-0003", "name": "Sales Team", "type": "official", "visibility": "public", "memberCount": 4},
    {"id": "group-0004", "name": "All Hands", "type": "official", "visibility": "public", "memberCount": 20},
    {"id": "group-0005", "name": "Weekend Coverage", "type": "custom", "visibility": "public", "memberCount": 6},
]

DEMO_QUEUES = [
    {"id": "queue-0001", "name": "General Support", "memberCount": 15},
    {"id": "queue-0002", "name": "Billing", "memberCount": 8},
    {"id": "queue-0003", "name": "Sales Inbound", "memberCount": 5},
    {"id": "queue-0004", "name": "Technical", "memberCount": 6},
    {"id": "queue-0005", "name": "VIP", "memberCount": 3},
]

DEMO_SKILLS = [
    {"id": "skill-0001", "name": "Phone", "state": "active"},
    {"id": "skill-0002", "name": "Email", "state": "active"},
    {"id": "skill-0003", "name": "Chat", "state": "active"},
    {"id": "skill-0004", "name": "Billing", "state": "active"},
    {"id": "skill-0005", "name": "Technical", "state": "active"},
]

_demo_mode = False


@anvil.server.callable
def set_demo_mode(enabled):
    """Enable or disable demo mode"""
    global _demo_mode
    _demo_mode = enabled
    return {'success': True}


@anvil.server.callable
def is_demo_mode():
    """Check if demo mode is enabled"""
    return _demo_mode


# Override API functions in demo mode

@anvil.server.callable
def demo_users_list_page(page_size=25, page_number=1):
    """Demo: Get paginated list of users"""
    start = (page_number - 1) * page_size
    end = start + page_size
    return {
        'success': True,
        'data': {
            'entities': DEMO_USERS[start:end],
            'total': len(DEMO_USERS),
            'pageCount': (len(DEMO_USERS) + page_size - 1) // page_size,
            'pageNumber': page_number,
            'pageSize': page_size
        }
    }


@anvil.server.callable
def demo_users_search_by_email(email):
    """Demo: Search for user by email"""
    for user in DEMO_USERS:
        if user['email'].lower() == email.lower():
            return {'success': True, 'data': user}
    return {'success': False, 'error': 'User not found'}


@anvil.server.callable
def demo_users_update(user_id, data):
    """Demo: Update user (just simulate success)"""
    for user in DEMO_USERS:
        if user['id'] == user_id:
            user.update(data)
            return {'success': True, 'data': user}
    return {'success': False, 'error': 'User not found'}


@anvil.server.callable
def demo_users_bulk_update(updates):
    """Demo: Bulk update users"""
    results = []
    for update in updates:
        result = demo_users_update(update['user_id'], update['payload'])
        results.append({
            'user_id': update['user_id'],
            'success': result['success'],
            'error': result.get('error')
        })

    success_count = sum(1 for r in results if r['success'])
    return {
        'success': True,
        'total': len(results),
        'success_count': success_count,
        'error_count': len(results) - success_count,
        'results': results
    }


@anvil.server.callable
def demo_groups_list_page(page_size=25, page_number=1):
    """Demo: Get paginated list of groups"""
    return {
        'success': True,
        'data': {
            'entities': DEMO_GROUPS,
            'total': len(DEMO_GROUPS),
            'pageCount': 1,
            'pageNumber': 1,
            'pageSize': page_size
        }
    }


@anvil.server.callable
def demo_groups_get_members(group_id):
    """Demo: Get group members"""
    # Return random users as members
    return {'success': True, 'data': DEMO_USERS[:8]}


@anvil.server.callable
def demo_queues_list_page(page_size=25, page_number=1):
    """Demo: Get paginated list of queues"""
    return {
        'success': True,
        'data': {
            'entities': DEMO_QUEUES,
            'total': len(DEMO_QUEUES),
            'pageCount': 1,
            'pageNumber': 1,
            'pageSize': page_size
        }
    }


@anvil.server.callable
def demo_routing_get_skills():
    """Demo: Get all routing skills"""
    return {'success': True, 'data': DEMO_SKILLS}
