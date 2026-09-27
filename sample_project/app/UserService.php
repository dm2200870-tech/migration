<?php

class UserService
{
    public function profile(array $user): array
    {
        return [
            "name" => $user["name"],
            "phone" => $user["phone"],
        ];
    }
}
