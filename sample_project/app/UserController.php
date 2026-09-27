<?php

class UserController
{
    public function show(array $user): array
    {
        return [
            "id" => $user["id"],
            "phone" => $user["phone"],
        ];
    }
}
