<?php

namespace ThoughtBundle\Form\User;

use Application\Sonata\UserBundle\Entity\User;
use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\Extension\Core\Type\ChoiceType;
use Symfony\Component\Form\Extension\Core\Type\SubmitType;
use Symfony\Component\Form\Extension\Core\Type\TextareaType;
use Symfony\Component\Form\Extension\Core\Type\TextType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolver;

class UserInfoForm extends AbstractType
{
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            ->add('about', TextareaType::class, [
                'label'      => 'user.form.profile.about.label',
                'required' => false,
            ])
            ->add('country', TextType::class, [
                'label'      => 'user.form.profile.country.label',
                'required' => false,
            ])
            ->add('interests', TextType::class, [
                'label'      => 'user.form.profile.interests.label',
                'required' => false,
            ])
            ->add('gender', ChoiceType::class, [
                'choices' => [
                    User::GENDER_MALE   => 'user.form.profile.gender.genderm',
                    User::GENDER_FEMALE => 'user.form.profile.gender.genderf',
                ],
                'required' => false,
            ])
            ->add('Save', SubmitType::class, [
                'attr' => [
                    'class' => 'btn-info',
                ],
            ])
        ;
    }

    /**
     * @inheritdoc
     */
    public function configureOptions(OptionsResolver $resolver)
    {
        $resolver->setDefaults([
            'data_class' => 'Application\Sonata\UserBundle\Entity\User',
        ]);
    }
}