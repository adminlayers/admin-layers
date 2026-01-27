# Genesys Admin Flows & Endpoint Map

This document maps every Admin Layers action to the Genesys Cloud endpoints it uses, with the UI flows followed in the app. It also calls out confirmation steps and the user detail actions for adding users to groups, skills, and queues.

## SaaS & Local User Storage

**Local user profile storage** is used to support SaaS-style usage by keeping a lightweight user profile on the client device (encrypted at rest). The profile is optional and stored locally so an operator’s identity follows the session without sending data to third-party systems.

**Flow**
1. User opens **Connect** → **Local User Profile**.
2. Profile is saved locally (encrypted).
3. Sidebar displays the active local profile for context.
4. Profile can be cleared at any time.

Endpoints: _none (local storage only)_

---

## OAuth Entry (Client Credentials)

**Flow**
1. User opens **Connect** → **OAuth Client Credentials**.
2. Enters Client ID, Client Secret, and Region.
3. App exchanges credentials for an access token.
4. Session starts and utilities become available.

Endpoints
- `POST /oauth/token`

---

## Users

### List Users (Paged)
**Flow**
1. **User Manager → All Users**.
2. Page size defaults to 25; user can switch to 50 or 100.
3. Page number controls request additional pages.

Endpoints
- `GET /api/v2/users?pageSize={25|50|100}&pageNumber={n}`

### View User Details
**Flow**
1. Select a user from the list or search.
2. **User Profile** view loads full user payload.

Endpoints
- `GET /api/v2/users/{userId}`

### Edit User Details
**Flow**
1. From the user action bar select **Edit**.
2. Update common fields (name, department, title, state).
3. Confirm and save.

Endpoints
- `PATCH /api/v2/users/{userId}`

### Add User to Group (from User Profile)
**Flow**
1. User opens **User Profile → Quick Actions → Add to Group**.
2. Search groups by name.
3. Confirm and add the user.

Endpoints
- `POST /api/v2/groups/{groupId}/members`

### Assign Skill to User (from User Profile)
**Flow**
1. User opens **User Profile → Quick Actions → Assign Skill**.
2. Select skill and proficiency.
3. Confirm and assign.

Endpoints
- `POST /api/v2/users/{userId}/routingskills`

### Add User to Queue (from User Profile)
**Flow**
1. User opens **User Profile → Quick Actions → Add to Queue**.
2. Search queues by name.
3. Confirm and add.

Endpoints
- `POST /api/v2/routing/queues/{queueId}/members`

---

## Groups

### List Groups (Paged)
**Flow**
1. **Group Manager → All Groups**.
2. Page size defaults to 25; user can switch to 50 or 100.
3. Page number controls request additional pages.

Endpoints
- `GET /api/v2/groups?pageSize={25|50|100}&pageNumber={n}`

### View Group Members
**Flow**
1. Open a group.
2. Members load on the **Members** page.

Endpoints
- `GET /api/v2/groups/{groupId}`
- `GET /api/v2/groups/{groupId}/members`

### Create Group (Confirm Required)
**Flow**
1. **Group Manager → Create Group**.
2. Enter name, description, type, and visibility.
3. Confirm warning and create.

Endpoints
- `POST /api/v2/groups`

### Edit Group (Common Settings)
**Flow**
1. Open a group and click **Edit** in the action bar.
2. Update name, description, visibility.
3. Save.

Endpoints
- `PATCH /api/v2/groups/{groupId}`

### Delete Group (Confirm Required)
**Flow**
1. Open a group → **Delete Group**.
2. Confirm deletion warning.

Endpoints
- `DELETE /api/v2/groups/{groupId}`

### Add/Remove Group Members
**Flow**
- Add: Use **Add Members** (paste/upload emails) and execute.
- Remove: Select members, confirm, and remove.

Endpoints
- `POST /api/v2/groups/{groupId}/members`
- `DELETE /api/v2/groups/{groupId}/members?ids={userIds}`

---

## Queues

### List Queues (Paged)
**Flow**
1. **Queue Manager → All Queues**.
2. Page size defaults to 25; user can switch to 50 or 100.
3. Page number controls request additional pages.

Endpoints
- `GET /api/v2/routing/queues?pageSize={25|50|100}&pageNumber={n}`

### View Queue Members
**Flow**
1. Open a queue.
2. Members load on the **Members** page.

Endpoints
- `GET /api/v2/routing/queues/{queueId}`
- `GET /api/v2/routing/queues/{queueId}/members`

### Create Queue (Confirm Required)
**Flow**
1. **Queue Manager → Create Queue**.
2. Enter name, description, and common routing settings.
3. Confirm warning and create.

Endpoints
- `POST /api/v2/routing/queues`

### Edit Queue (Common Settings)
**Flow**
1. Open a queue and click **Edit** in the action bar.
2. Update name, description, skill evaluation, and timeouts.
3. Save.

Endpoints
- `PATCH /api/v2/routing/queues/{queueId}`

### Delete Queue (Confirm Required)
**Flow**
1. Open a queue → **Delete Queue**.
2. Confirm deletion warning.

Endpoints
- `DELETE /api/v2/routing/queues/{queueId}`

### Add/Remove Queue Members
**Flow**
- Add: Use **Add Members** (paste/upload emails) and execute.
- Remove: Select members, confirm, and remove.

Endpoints
- `POST /api/v2/routing/queues/{queueId}/members`

---

## Skills

### List Skills (Paged)
**Flow**
1. **Skill Manager → All Skills**.
2. Page size defaults to 25; user can switch to 50 or 100.
3. Page number controls request additional pages.

Endpoints
- `GET /api/v2/routing/skills?pageSize={25|50|100}&pageNumber={n}`

### View Skill Details
**Flow**
1. Open a skill from the list.
2. View details in the **Skill Details** page.

Endpoints
- `GET /api/v2/routing/skills/{skillId}`

### Create Skill (Confirm Required)
**Flow**
1. **Skill Manager → Create Skill**.
2. Enter name, description, state.
3. Confirm warning and create.

Endpoints
- `POST /api/v2/routing/skills`

### Edit Skill (Common Settings)
**Flow**
1. Open a skill and click **Edit** in the action bar.
2. Update name, description, and state.
3. Save.

Endpoints
- `PUT /api/v2/routing/skills/{skillId}`

### Delete Skill (Confirm Required)
**Flow**
1. Open a skill → **Delete Skill**.
2. Confirm deletion warning.

Endpoints
- `DELETE /api/v2/routing/skills/{skillId}`

### Assign/Remove Skill (Bulk)
**Flow**
- Assign: Select skill, enter emails, confirm dry run/execute.
- Remove: Select skill, enter emails, confirm removal.

Endpoints
- `POST /api/v2/users/{userId}/routingskills`
- `DELETE /api/v2/users/{userId}/routingskills/{skillId}`
