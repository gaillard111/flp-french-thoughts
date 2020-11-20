<?php

namespace ThoughtBundle\Service;

use Application\Sonata\UserBundle\Entity\User;
use Symfony\Component\Translation\TranslatorInterface;

class MenuService
{
    /**
     * @var TranslatorInterface
     */
    private $translator;

    public function __construct(TranslatorInterface $translator)
    {
        $this->translator = $translator;
    }

    /**
     * @return array
     */
    public function makeMenu(User $user)
    {
        $menu = [];

        $menu[] = [
            'label' => $this->translator->trans('navbar.profile'),
            'route' => 'my_settings',
        ];

        $menu[] = [
            'label'      => $this->translator->trans('user.form.profile.profile_edit'),
            'route'      => 'user_profile',
            'parameters' => [
                'userId' => $user->getId(),
            ],
        ];

        if (in_array('ROLE_TEACHER', $user->getRoles())) {
            $menu[] = [
                'label' =>  $this->translator->trans('teacher.group.title'),
                'route' => 'teacher_groups_list'
            ];
        }

        if (in_array('ROLE_STUDENT', $user->getRoles())) {
            $menu[] = [
                'label' => $this->translator->trans('student.group.title'),
                'route' => 'my_groups',
            ];
        }

        $menu[] = [
            'label' => $this->translator->trans('user.friendship.title'),
            'route' => 'friends',
        ];

        $menu[] = [
            'label' => $this->translator->trans('user.dialogs.title'),
            'route' => 'chat_list',
        ];

        $menu[] = [
            'label' => $this->translator->trans('user.thought.create_page.title'),
            'route' => 'sonata_user_thought_create',
        ];

        $menu[] = [
            'label' => $this->translator->trans('user.thought.list_page.title'),
            'route' => 'profile_thoughts_list',
        ];

        $menu[] = [
            'label' => $this->translator->trans('thought.menu.favorite_thoughts'),
            'route' => 'favorite-list',
        ];

        $menu[] = [
            'label' => $this->translator->trans('user.topic.list_page.title'),
            'route' => 'profile_topics_list',
        ];

        $menu[] = [
            'label' => $this->translator->trans('user.chain.list_page.title'),
            'route' => 'sonata_user_chains',
        ];

        return $menu;
    }
}