<?php

namespace ThoughtBundle\Form\Teacher;

use Application\Sonata\UserBundle\Entity\User;
use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\Extension\Core\Type\SubmitType;
use Symfony\Component\Form\FormBuilderInterface;
use Tetranz\Select2EntityBundle\Form\Type\Select2EntityType;

class StudentSearchForm extends AbstractType
{
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            ->add('searchField',Select2EntityType::class, [
                'class' => User::class,
                'placeholder' => 'Search student',
                'remote_route' => 'student_search',
                'width' => '330',
                'label' => false,
            ])
            ->add('add', SubmitType::class, []);
    }
}